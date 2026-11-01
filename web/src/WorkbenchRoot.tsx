import {lazy,Suspense,useEffect,useState} from 'react';
import {ArrowUpRight,BookOpen,Globe2} from 'lucide-react';
import './workbench.css';
const FdiWorkspace=lazy(()=>import('./fdi/FdiWorkspace'));
export default function WorkbenchRoot({financial:Financial}:{financial:React.ComponentType}){
 const [hash,setHash]=useState(location.hash);
 useEffect(()=>{const change=()=>setHash(location.hash);window.addEventListener('hashchange',change);return()=>window.removeEventListener('hashchange',change)},[]);
 if(hash.startsWith('#/fdi/'))return <Suspense fallback={<main className="research-hub"><p>Opening the FDI observatory…</p></main>}><FdiWorkspace/></Suspense>;
 if(hash&&hash!=='#/'&&hash!=='#/hub')return <Financial/>;
 return <main className="research-hub"><a className="hub-home" href="https://nandolab.github.io/">Fernando Barbosa <ArrowUpRight size={14}/></a><p className="hub-kicker">Independent research</p><h1>Research Workbench</h1><p className="hub-lede">Two research collections. Clear questions, inspectable evidence and reproducible analysis.</p><div className="hub-workspaces"><a href="#/overview"><BookOpen size={28}/><h2>Financial Intelligence</h2><p>Read the evidence behind research on banks and insurers. Inspect the recorded model comparisons, named entities and retrieval results.</p><span>Explore financial research <ArrowUpRight size={16}/></span></a><a href="#/fdi/overview"><Globe2 size={28}/><h2>Foreign Direct Investment</h2><p>Explore thirty years of investment into Brazil: its international origins, economic geography, drivers and effects.</p><span>Open the economic atlas <ArrowUpRight size={16}/></span></a></div><p className="hub-footnote">Research collections retain their own sources, methods and validation boundaries.</p></main>
}
