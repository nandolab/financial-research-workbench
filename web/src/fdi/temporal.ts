const finite=(v:unknown):v is number=>typeof v==='number'&&Number.isFinite(v);
export type TemporalRow={country:string;year:number;[key:string]:number|string|null};
export const monetaryViews={
 constant_usd:{label:'Constant 2025 US dollars',unit:'2025 US$ billion',scale:1e9,explanation:'Annual net inflows adjusted with the BEA US GDP implicit price deflator (via FRED), rebased to 2025. This holds the US price basis constant; it is not PPP or a physical investment-volume measure.'},
 current_usd:{label:'Current US dollars',unit:'Current US$ billion',scale:1e9,explanation:'The original World Bank WDI annual net-inflow observations. Changes combine investment, prices and exchange-rate effects.'},
 constant_usd_per_person:{label:'Constant 2025 US$ per resident',unit:'2025 US$ per resident',scale:1,explanation:'Constant-dollar inflows divided by observed WDI total population in the same year. Missing population stays missing. This adjusts for population size, not income distribution.'},
 flow_gdp:{label:'FDI as a share of GDP',unit:'% of GDP',scale:1,explanation:'WDI net inflows relative to contemporaneous nominal GDP. This compares investment with the size of the economy; it is not a constant-dollar measure.'},
 constant_brl:{label:'Constant 2025 reais (IPCA)',unit:'2025 R$ billion',scale:1e9,explanation:'BCB monthly net inflows × monthly average BRL/US$ × average 2025 IPCA / that month’s IPCA, then summed. All 12 months are required. This is a Brazilian consumer-price perspective; exchange-rate effects remain and IPCA is not a capital-goods deflator.'},
} as const;
export type MonetaryView=keyof typeof monetaryViews;
export function temporalWindow(params:URLSearchParams){
 const year=(key:string,fallback:number)=>{const v=Number(params.get(key));return params.has(key)&&Number.isInteger(v)&&v>=1996&&v<=2025?v:fallback};
 const start=year('from',1996),end=year('to',2025);return start<=end?{start,end}:{start:1996,end:2025};
}
export function windowStats(rows:TemporalRow[],key:string,start:number,end:number){
 const selected=rows.filter(r=>r.year>=start&&r.year<=end).sort((a,b)=>a.year-b.year);
 const observed=selected.filter(r=>finite(r[key]));const first=selected[0],last=selected.at(-1);
 const complete=selected.length===end-start+1&&selected.every((r,i)=>r.year===start+i&&finite(r[key]));
 const positive=complete&&selected.every(r=>(r[key] as number)>0);
 const cagr=positive&&end>start?100*(Math.pow((last![key] as number)/(first[key] as number),1/(end-start))-1):null;
 const latest=observed.at(-1);const previous=latest&&selected.find(r=>r.year===latest.year-1);
 const change=latest&&previous&&finite(previous[key])?(latest[key] as number)-(previous[key] as number):null;
 const average=observed.length?observed.reduce((sum,r)=>sum+(r[key] as number),0)/observed.length:null;
 return {latest,change,cagr,average,observed:observed.length,expected:end-start+1,complete};
}
