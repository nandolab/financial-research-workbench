"""Publication figures derived only from strict-reviewed, real Colab exports."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon


def figures(folder):
    folder=Path(folder);source=folder/'observatory.json';d=json.loads(source.read_text(encoding='utf8'))
    if d['national'].get('review',{}).get('state')!='passed':raise ValueError('Strict reviewed national export required')
    plt.rcParams.update({'font.family':'DejaVu Sans','svg.fonttype':'none','axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#586374','text.color':'#081b41'})
    world=json.loads((folder/'world.geo.json').read_text(encoding='utf8'))
    year=2025;colors=['#167c80','#8464a0'];countries={c['id']:c for c in d['countries']}
    fig=plt.figure(figsize=(12,8),layout='constrained');gs=fig.add_gridspec(2,2,width_ratios=[1.5,1])
    for i,basis in enumerate(['immediate','ultimate']):
        ax=fig.add_subplot(gs[i,0])
        for feature in world['features']:
            geometry=feature['geometry'];polygons=[geometry['coordinates']] if geometry['type']=='Polygon' else geometry['coordinates']
            for rings in polygons:ax.add_patch(Polygon(rings[0],facecolor='#e7ebef',edgecolor='white',linewidth=.3))
        points=[r for r in d['origins'] if r['year']==year and r['basis']==basis and r['country'] in countries]
        for r in points:
            c=countries[r['country']]
            if c['longitude'] is not None and c['latitude'] is not None:
                ax.scatter(c['longitude'],c['latitude'],s=max(1,240*abs(r['value_usd'])/1e11),color=colors[i],alpha=.55,edgecolor='white',linewidth=.4)
        ax.set(xlim=(-180,180),ylim=(-58,85),title=basis.capitalize()+' investor attribution');ax.set_aspect('equal');ax.axis('off')
        handles=[ax.scatter([],[],s=240*v/100,color=colors[i],alpha=.55,label=f'US${v}bn') for v in [25,100]]
        ax.legend(handles=handles,loc='lower left',frameon=False,ncol=2,fontsize=8)
    ax=fig.add_subplot(gs[:,1]);immediate={r['name']:r['value_usd']/1e9 for r in d['origins'] if r['year']==year and r['basis']=='immediate'};ultimate={r['name']:r['value_usd']/1e9 for r in d['origins'] if r['year']==year and r['basis']=='ultimate'}
    names=sorted(set(immediate)&set(ultimate),key=lambda n:max(immediate[n],ultimate[n]),reverse=True)[:9][::-1]
    for y,name in enumerate(names):
        ax.plot([immediate[name],ultimate[name]],[y,y],color='#bdc8d0',linewidth=2)
    ax.scatter([immediate[n] for n in names],range(len(names)),c=colors[0],label='Immediate',zorder=3)
    ax.scatter([ultimate[n] for n in names],range(len(names)),c=colors[1],label='Ultimate',zorder=3)
    ax.set_yticks(range(len(names)),names);ax.set_xlabel('Inward equity position · US$ billion');ax.legend(frameon=False);ax.grid(axis='x',alpha=.15)
    fig.suptitle('Origins of invested equity in Brazil, 2025',fontsize=17)
    fig.supxlabel('Source: BCB IDP positions · Country points are representative locations, not transaction routes.\nMatched equity definitions and reference year · Fernando Barbosa',fontsize=9)
    outputs=[]
    for ext in ['svg','png']:
        p=folder/f'02-investor-origin-map.{ext}';fig.savefig(p,dpi=180);outputs.append(p)
    plt.close(fig)
    m=d['national'];h=np.arange(13);response=1;shock=4
    fig,ax=plt.subplots(figsize=(10,6),layout='constrained')
    for lower,upper,color,label in [('.025','.975','#dceae9','Pointwise 95% bootstrap interval'),('.16','.84','#a2ceca','Pointwise 68% bootstrap interval')]:
        # Native JSON quantile keys include the leading zero.
        lo=np.asarray(m['irf_intervals']['0'+lower])[:,response,shock];hi=np.asarray(m['irf_intervals']['0'+upper])[:,response,shock]
        ax.fill_between(h,lo,hi,color=color,label=label)
    ax.plot(h,np.asarray(m['irf'])[:,response,shock],c=colors[0],label='Structural VAR response',linewidth=2)
    ax.axhline(0,c='#728594',linewidth=.8);ax.set(xlabel='Quarters after the innovation',ylabel='Real GDP growth response · percentage points',xticks=h)
    ax.legend(frameon=False,fontsize=9);ax.grid(axis='y',alpha=.15)
    fig.suptitle('Brazil GDP growth after an identified FDI innovation',fontsize=16)
    fig.supxlabel('2,000 valid bootstrap draws · Recursive restrictions apply; the impact response is zero by assumption.\nOne-standard-deviation innovation = 1.18 pp of quarterly FDI/GDP · Fernando Barbosa',fontsize=9)
    for ext in ['svg','png']:
        p=folder/f'03-national-gdp-response.{ext}';fig.savefig(p,dpi=180);outputs.append(p)
    plt.close(fig)
    report={'source_export_identity':d['export_identity'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'figures':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in outputs},
        'municipal_event_study':'not rendered; identification inputs unavailable'}
    (folder/'publication-figures.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);figures(p.parse_args().data)
