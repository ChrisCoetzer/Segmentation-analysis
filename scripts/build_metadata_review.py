"""Build review tables, example metadata, and figures from raw-data aggregates."""
from pathlib import Path
import json, os
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/metadata_exploration'
OUT.mkdir(exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'matplotlib_cache'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

READINESS=['Unengaged prospects','Light browsers','Active researchers','Decision-stage shoppers','High-intent shoppers']
MISSIONS=['Quiet prospects','Independent light browsers','Engageable light browsers','Self-directed researchers','Engageable researchers','Self-directed buyers','Responsive buyers']
STYLES=['Self-directed','Low-engagement','Ad-receptive']
COLS=['n','treated','visits','conversions','exposed','treated_visits','treated_conversions']

def assign(d,flags=True):
    if flags:
        f={x:d[x+'_active'].eq(1).to_numpy() for x in ['f8','f9','f4','f11','f3','f6']}
    else:
        modes=json.loads((OUT/'rules.json').read_text())['modes']
        f={x:d[x].ne(modes[x]).to_numpy() for x in ['f8','f9','f4','f11','f3','f6']}
    r=np.select([~f['f8'],~f['f9'],~f['f4'],~f['f11']],[0,1,2,3],default=4)
    independent=~f['f3']&~f['f6']
    m=np.select([r==0,(r==1)&independent,r==1,(r==2)&independent,r==2,(r>=3)&independent],[0,1,2,3,4,5],default=6)
    style=np.select([independent,~f['f3']],[0,1],default=2)
    return r,m,style

def summary(p,key):
    g=p.groupby(['partition',key])[COLS].sum().reset_index()
    g['share_pct']=100*g.n/g.groupby('partition').n.transform('sum')
    for o in ['visits','conversions']:
        a=g['treated_'+o]/g.treated;b=(g[o]-g['treated_'+o])/(g.n-g.treated)
        g[o+'_pct']=100*g[o]/g.n;g[o+'_treatment_pct']=100*a;g[o+'_control_pct']=100*b
        g[o+'_effect_per_10k']=10000*(a-b)
        g[o+'_se_per_10k']=10000*np.sqrt(a*(1-a)/g.treated+b*(1-b)/(g.n-g.treated))
        g[o+'_share_pct']=100*g[o]/g.groupby('partition')[o].transform('sum')
    return g

def style_axes(ax):
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color('#d0d7df')
    ax.tick_params(colors='#334155',length=0,pad=7)
    ax.xaxis.grid(True,color='#e7ecf1');ax.set_axisbelow(True)

def main():
    p=pd.read_csv(OUT/'feature_patterns.csv')
    p['readiness'],p['mission'],p['style']=assign(p)
    tables={key:summary(p,key) for key in ['readiness','mission','style']}
    for key,g in tables.items():
        names={'readiness':READINESS,'mission':MISSIONS,'style':STYLES}[key]
        g['synthetic_label']=g[key].map(dict(enumerate(names)))
        g.to_csv(OUT/(key+'_summary.csv'),index=False)
    joint=p.groupby(['partition','readiness','style'])[COLS].sum().reset_index()
    joint.to_csv(OUT/'readiness_style_cells.csv',index=False)
    sample=pd.read_parquet(OUT/'feature_sample.parquet').sample(20000,random_state=20261116).copy()
    r,m,s=assign(sample,flags=False)
    sample['synthetic_audience_stage']=np.array(READINESS)[r]
    sample['synthetic_campaign_role']=np.array(MISSIONS)[m]
    sample['synthetic_engagement_style']=np.array(STYLES)[s]
    themes=['Brand introduction','Product overview','Benefit-led exploration','Research content','Product comparison','Convenience reminder','Purchase reminder']
    needs=['Discover why the retailer is relevant','Browse with minimal interruption','Find a reason to explore further','Understand product details independently','Compare benefits and reduce uncertainty','Complete a familiar task conveniently','Receive a timely prompt to complete a decision']
    objectives=['Awareness','Low-touch exploration','Visits','Informational support','Visits','Convenience','Conversions']
    sample['proposed_message_theme']=np.array(themes)[m]
    sample['fictional_customer_need']=np.array(needs)[m]
    sample['proposed_campaign_objective']=np.array(objectives)[m]
    sample['metadata_origin']='Synthetic scenario labels assigned to real feature patterns; message effectiveness not measured'
    sample=sample.drop(columns=['cluster8']+[c for c in sample if c.endswith('_active')])
    sample['partition']=sample.partition.map({0:'train',1:'estimation',2:'evaluation'})
    sample.to_csv(OUT/'metadata_example_20000.csv',index=False)
    catalogue=dict(origin='Synthetic scenario vocabulary. Motivations and creative effectiveness are not measured.',readiness_stages=READINESS,engagement_styles=STYLES,campaign_roles=[dict(id=i,label=label,fictional_customer_need=needs[i],proposed_message_theme=themes[i],proposed_campaign_objective=objectives[i]) for i,label in enumerate(MISSIONS)])
    (OUT/'metadata_catalogue.json').write_text(json.dumps(catalogue,indent=2))
    # Scientific figures: measured rates are kept separate from fictional labels.
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':12,'axes.labelsize':11,'figure.facecolor':'#ffffff','axes.facecolor':'#ffffff','text.color':'#172b4d','axes.labelcolor':'#334155'})
    a=tables['readiness'].query('partition=="evaluation"').sort_values('readiness')
    fig,axes=plt.subplots(1,3,figsize=(15.5,5.3),sharey=True,gridspec_kw={'width_ratios':[1,1,1]})
    yy=np.arange(5)
    for ax,metric,title,color in zip(axes,['share_pct','visits_pct','conversions_pct'],['Share of audience (%)','Observed visit rate (%)','Observed conversion rate (%)'],['#64748b','#2563eb','#0f766e']):
        ax.barh(yy,a[metric],color=color,height=.55)
        ax.set_title(title,pad=15);ax.set_xlim(0,a[metric].max()*1.24)
        for y,x in zip(yy,a[metric]):ax.text(x+a[metric].max()*.025,y,f'{x:.2f}',va='center')
        style_axes(ax)
    axes[0].set_yticks(yy,READINESS);axes[0].invert_yaxis()
    fig.suptitle('Option 1 | A small purchase-ready audience, a large discovery audience',fontsize=16,x=.03,ha='left',y=.98)
    fig.text(.03,.025,'Synthetic audience names. Actual counts and outcomes: 2,795,919 evaluation records. Groups are feature-defined, not observed journey stages.',fontsize=10,color='#475569')
    fig.tight_layout(rect=[0,.07,1,.91]);fig.savefig(OUT/'option_1_readiness.png',dpi=170,bbox_inches='tight');plt.close(fig)
    b=tables['mission'].query('partition=="evaluation"').sort_values('mission')
    fig,axes=plt.subplots(1,3,figsize=(16,6),sharey=True,gridspec_kw={'width_ratios':[.8,1.1,1.1]})
    yy=np.arange(7)
    axes[0].barh(yy,b.share_pct,color='#64748b',height=.55);axes[0].set_title('Share of audience (%)',pad=15)
    for y,x in zip(yy,b.share_pct):axes[0].text(x+.5,y,f'{x:.1f}',va='center')
    axes[0].set_xlim(0,64)
    for ax,outcome,title in zip(axes[1:],['visits','conversions'],['Visit rate (%)','Conversion rate (%)']):
        c=b[outcome+'_control_pct'].to_numpy();t=b[outcome+'_treatment_pct'].to_numpy()
        ax.hlines(yy,c,t,color='#b7c2cf',linewidth=3)
        ax.scatter(c,yy,label='Control',color='#64748b',s=42,zorder=3)
        ax.scatter(t,yy,label='Treatment',color='#2563eb',marker='D',s=42,zorder=3)
        ax.set_title(title,pad=15);ax.set_xlim(-.01,max(t)*1.15)
    axes[2].legend(loc='upper right',frameon=False)
    for ax in axes:style_axes(ax)
    axes[0].set_yticks(yy,MISSIONS);axes[0].invert_yaxis()
    fig.suptitle('Option 2 | Frequent visitors and responsive audiences are different campaign roles',fontsize=16,x=.03,ha='left',y=.98)
    fig.text(.03,.025,'Synthetic role names. Actual treatment/control comparisons from evaluation records; descriptive benchmark results, not tested message effects.',fontsize=10,color='#475569')
    fig.tight_layout(rect=[0,.07,1,.91]);fig.savefig(OUT/'option_2_missions.png',dpi=170,bbox_inches='tight');plt.close(fig)
    j=pd.read_csv(OUT/'journey_archetypes.csv');freq=['1','2-3','4-10','11+']
    j=j.sort_values(['clicked','frequency'],key=lambda c:c.map(dict(zip(freq,range(4)))) if c.name=='frequency' else c).reset_index(drop=True)
    labels=[('Clicked' if row.clicked else 'No recorded click')+' | '+row.frequency+(' ad' if row.frequency=='1' else ' ads') for row in j.itertuples()]
    fig,axes=plt.subplots(1,2,figsize=(13,5.8),sharey=True)
    yy=np.arange(8);share=100*j.pairs/j.pairs.sum();rate=100*j.positive_pair_rate
    for ax,values,title,color in zip(axes,[share,rate],['Share of user-campaign pairs (%)','Conversion-positive pair rate (%)'],['#64748b','#0f766e']):
        ax.barh(yy,values,color=color,height=.55);ax.set_title(title,pad=15);ax.set_xlim(0,max(values)*1.22)
        for y,x in zip(yy,values):ax.text(x+max(values)*.025,y,f'{x:.2f}',va='center')
        style_axes(ax)
    axes[0].set_yticks(yy,labels);axes[0].invert_yaxis()
    fig.suptitle('Option 3 | Recorded engagement histories',fontsize=16,x=.03,ha='left',y=.98)
    fig.text(.03,.025,'7,813,401 user-campaign pairs from 16,468,027 impressions. Retrospective groups; association does not establish an advertising frequency effect.',fontsize=10,color='#475569')
    fig.tight_layout(rect=[0,.07,1,.91]);fig.savefig(OUT/'option_3_journeys.png',dpi=170,bbox_inches='tight');plt.close(fig)
    expected={'train':8387755,'estimation':2795918,'evaluation':2795919}
    for key,g in tables.items():
        assert g.groupby('partition').n.sum().to_dict()==expected
        assert np.isclose(g.groupby('partition').share_pct.sum(),100).all()
        assert (g.treated<=g.n).all() and (g.treated_conversions<=g.conversions).all()
    assert int(p.n.sum())==13979592
    assert int(j.pairs.sum())==7813401 and int(j.impressions.sum())==16468027
    assert sample.source_row_index.is_unique
    checks={'all_uplift_rows_accounted_for':int(p.n.sum()),'partitions':expected,'all_three_group_schemes_exhaustive':True,'journey_pairs':int(j.pairs.sum()),'journey_impressions':int(j.impressions.sum()),'metadata_sample_rows':len(sample),'real_outcomes_modified':False,'application_modified':False}
    (OUT/'validation.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
