# Callaway--Sant'Anna group-time ATT. No placeholder estimates or automatic TWFE fallback.
args <- commandArgs(trailingOnly=TRUE)
if (length(args)!=3) stop('Usage: municipal_did.R panel.csv config.json output.json')
library(jsonlite)
if (!requireNamespace('did', quietly=TRUE)) stop('Install pinned did 2.5.1 first')
if (as.character(utils::packageVersion('did')) != '2.5.1') stop('did version differs from frozen specification')
config <- jsonlite::fromJSON(args[2])
dat <- read.csv(args[1], stringsAsFactors=FALSE)
required <- c('municipality_id','year','opening_year',unlist(config$models$municipal_did$covariates))
if (!all(required %in% names(dat))) stop('Panel lacks required identifiers/pretreatment covariates')
if (anyDuplicated(dat[c('municipality_id','year')])) stop('Duplicate municipality-year')
dat$municipality_id <- as.integer(dat$municipality_id)
dat$opening_year[is.na(dat$opening_year)] <- 0
formula <- as.formula(paste('~',paste(unlist(config$models$municipal_did$covariates),collapse='+')))
results <- list()
for (outcome in unlist(config$models$municipal_did$outcomes)) {
  if (!(outcome %in% names(dat))) {
    results[[outcome]] <- list(state='unavailable', reason='Verified outcome series not supplied')
    next
  }
  sample <- dat[complete.cases(dat[c(required,outcome)]),]
  tryCatch({
    set.seed(config$seed)
    att <- did::att_gt(yname=outcome, tname='year', idname='municipality_id', gname='opening_year', data=sample,
      xformla=formula, panel=TRUE, allow_unbalanced_panel=FALSE, control_group='notyettreated',
      anticipation=2, est_method='dr', base_period='universal', bstrap=TRUE, cband=TRUE,
      biters=config$bootstrap_replications, clustervars='municipality_id', print_details=FALSE, cores=1)
    dynamic <- did::aggte(att,type='dynamic', min_e=-7,max_e=5, balance_e=5, na.rm=FALSE)
    post <- did::aggte(att,type='dynamic', min_e=1,max_e=5,balance_e=5,na.rm=FALSE)
    if (any(!is.finite(dynamic$att.egt)) || any(!is.finite(dynamic$se.egt))) stop('Nonfinite treatment effects or uncertainty; inspect support')
    results[[outcome]] <- list(state='estimated_conditional_on_assumptions',estimand='Effect of qualifying operational openings, not effect per dollar FDI',
      periods=dynamic$egt,att=dynamic$att.egt,se=dynamic$se.egt,simultaneous_critical_value=dynamic$crit.val.egt,
      overall=post$overall.att,overall_se=post$overall.se,pretest_pvalue=att$Wpval,
      municipalities=length(unique(sample$municipality_id)),treated=length(unique(sample$municipality_id[sample$opening_year>0])),
      comparison='never-treated and not-yet-treated',anticipation=2,reference_event_year=-3,
      assumptions=c('Conditional parallel trends','No effects before two-year anticipation window','No uncontrolled spillovers','Accurate treatment timing'))
  },error=function(e) {results[[outcome]] <<- list(state='unavailable',reason=conditionMessage(e))})
}
jsonlite::write_json(list(schema_version=1,estimator='Callaway-SantAnna did 2.5.1',outcomes=results),args[3],auto_unbox=TRUE,pretty=TRUE,na='null',digits=15)
