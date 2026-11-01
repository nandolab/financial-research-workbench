export type Observation = {country:string;year:number;flow_usd?:number|null;flow_gdp?:number|null;gdp_usd?:number|null};
export type Country = {id:string;name:string;longitude:number|null;latitude:number|null;region:string};
export type Origin = {country:string|null;name:string;basis:string;year:number;value_usd:number;share:number|null};
export type Account = {id:string;name:string;year:number;population?:number|null;gdp_brl:number|null;gdp_per_capita?:number|null;gva_brl:number|null;industry_brl:number|null;agriculture_brl:number|null;services_brl:number|null;public_brl:number|null};
export type Sector = {id:string;name:string;group:string;level:number;year:number;value_usd:number;share:number|null};
export type Bundle = {
 schema_version:number;identity:string;built_at:string;window:number[];countries:Country[];annual:Observation[];
 components:Array<{year:number;total:number|null;equity_ex_reinvested:number|null;reinvested:number|null;debt:number|null}>;
 positions:Array<{year:number;total_usd:number;equity_usd:number;debt_usd:number}>;origins:Origin[];sectors:Sector[];
 joint:Array<{year:number;basis:string;country:string|null;country_name:string;sector:string;level:number;value_usd:number}>;
 states:Array<{id:string;name:string;abbreviation:string}>;state_accounts:Account[];
 state_measures:Array<{state:string;year:number;measure:string;value:number;definition:string;table:string}>;
 source_manifest:Record<string,{status:string;provider:string;url:string;definition:string;retrieved_at?:string;sha256?:string;reason?:string}>;
 national:any;municipal:any;study:any;causal_design?:any;validation:any;research_status:any;municipal_coverage:any;quarterly_coverage:any;
};
export const sections=['overview','global','brazil','drivers','effects','methods'] as const;
export type Section=typeof sections[number];
export const sectionLabels:Record<Section,string>={overview:'Overview',global:'Global Capital',brazil:'Brazil Atlas',drivers:'Investment Drivers',effects:'Economic Effects',methods:'Research & Methods'};
export function parseRoute(hash:string){
 const [path,q='']=hash.replace(/^#\//,'').split('?');const candidate=path.split('/')[1];const params=new URLSearchParams(q);
 for(const [key,min,max]of [['year',1996,2025],['localYear',2001,2025],['shock',0,4],['response',0,4],['lpExtra',0,2],['followLag',1,4]] as const){if(params.has(key)){const value=Number(params.get(key));if(!Number.isInteger(value)||value<min||value>max)params.delete(key)}}
 if(params.has('intervalMethod')&&!['legacy_hac_normal','hac_corrected_normal','hac_corrected_t','hc3_t','oracle_hac_corrected_t'].includes(params.get('intervalMethod')!))params.delete('intervalMethod');
 if(params.has('calibrationSample')&&!['paired','holdout'].includes(params.get('calibrationSample')!))params.delete('calibrationSample');
 if(params.has('responseView')&&!['gdp-level','unit-growth'].includes(params.get('responseView')!))params.delete('responseView');
 if(params.has('state')&&!/^(1[1-7]|2[1-9]|3[1-3]|35|4[1-3]|5[0-3])$/.test(params.get('state')!))params.delete('state');
 if(params.has('city')&&!/^\d{7}$/.test(params.get('city')!))params.delete('city');
 if(params.has('country')&&!/^[A-Z]{3}$/.test(params.get('country')!))params.delete('country');
 if(params.has('basis')&&!['immediate','ultimate'].includes(params.get('basis')!))params.delete('basis');
 return {section:sections.includes(candidate as Section)?candidate as Section:'overview',params};
}
export function readRoute(){return parseRoute(location.hash)}
export function updateRoute(section:Section,patch:Record<string,string|number|null>={}){const {params}=readRoute();for(const [k,v]of Object.entries(patch)){if(v===null)params.delete(k);else params.set(k,String(v))}location.hash=`/fdi/${section}${params.size?'?'+params:''}`}
export function finite(v:unknown):v is number{return typeof v==='number'&&Number.isFinite(v)}
export function axisTick(v:number){if(v===0)return '0';if(Math.abs(v)<.001)return v.toExponential(1);return Intl.NumberFormat('en',{notation:'compact',maximumFractionDigits:Math.abs(v)<1?3:1}).format(v)}
export function format(v:number|null|undefined,unit=''){if(!finite(v))return 'Not available';if(unit==='USD')return new Intl.NumberFormat('en',{style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:1}).format(v);if(unit==='BRL')return new Intl.NumberFormat('en',{style:'currency',currency:'BRL',notation:'compact',maximumFractionDigits:1}).format(v);return `${new Intl.NumberFormat('en',{maximumFractionDigits:2}).format(v)}${unit}`}
