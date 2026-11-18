"""Render scientific review figures and document synthetic replay comparisons."""
from pathlib import Path
import os,json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/campaign_timing'
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'matplotlib_cache'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def style(ax):
    ax.spines[['top','right']].set_visible(False)
    ax.spines[['left','bottom']].set_color('#cad3de')
    ax.grid(axis='y',color='#e8edf3');ax.set_axisbelow(True)
    ax.tick_params(length=0,pad=7)

def main():
    p=pd.read_parquet(OUT/'histories.parquet')
    campaign_start=p.groupby('campaign')['first'].min()
    p['campaign_start']=p.campaign.map(campaign_start)
    p['campaign_age_days']=(p['first']-p.campaign_start)/86400
    reach=[]
    for horizon in [14,28]:
        a=p[p.campaign_start.le(2671199-horizon*86400)&p.campaign_age_days.le(horizon)]
        for day in range(1,horizon+1):reach.append(dict(horizon=horizon,day=day,campaigns=a.campaign.nunique(),audience_pairs=len(a),pairs_reached=int(a.campaign_age_days.le(day).sum()),share_reached=float(a.campaign_age_days.le(day).mean())))
    pd.DataFrame(reach).to_csv(OUT/'campaign_audience_reach.csv',index=False)
    e=p[p.eligible14&p.event14]
    curves=pd.DataFrame([dict(day=d,response_observed_pct=100*e.event_days.le(d).mean(),last_ad_observed_pct=100*e.last_pre_event_contact_days.le(d).mean()) for d in range(15)])
    curves.to_csv(OUT/'response_vs_contact_duration.csv',index=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'figure.facecolor':'white','axes.facecolor':'white','text.color':'#172b4d','axes.labelcolor':'#334155','axes.titlesize':13})
    fig,axes=plt.subplots(1,2,figsize=(13,5.7))
    axes[0].plot(curves.day,curves.response_observed_pct,color='#2563eb',lw=2.7,label='Conversion recorded')
    axes[0].plot(curves.day,curves.last_ad_observed_pct,color='#0f766e',lw=2.7,label='Last pre-conversion ad recorded')
    axes[0].set(xlabel='Days since first recorded impression',ylabel='Share of 14-day response histories (%)',xlim=(0,14),ylim=(0,103),title='Response time and advertising time differ')
    axes[0].legend(frameon=False,loc='lower right')
    f=pd.read_csv(OUT/'event_contact_curve.csv');f=f[f.contacts<=10]
    axes[1].plot(f.contacts,100*f.share_of_events,marker='o',lw=2.7,color='#7c3aed')
    axes[1].set(xlabel='Recorded impressions before conversion',ylabel='Cumulative share of response histories (%)',xlim=(.8,10.2),ylim=(0,103),title='One contact covers only part of the histories')
    axes[1].annotate(f'{100*e.event_contact_number.eq(1).mean():.1f}% had one recorded contact',(1,100*e.event_contact_number.eq(1).mean()),xytext=(2,36),arrowprops=dict(arrowstyle='-',color='#64748b'))
    for ax in axes:style(ax)
    fig.suptitle('Campaign timing: an empirical foundation for the planning simulator',fontsize=16,x=.025,ha='left',y=.98)
    fig.text(.025,.025,'166,050 responding user-campaign histories; 4,941,310 histories had equal 14-day follow-up. Recorded contact patterns are not causal stopping effects.',fontsize=10,color='#475569')
    fig.tight_layout(rect=[0,.065,1,.92]);fig.savefig(OUT/'timing_foundation.png',dpi=170,bbox_inches='tight');plt.close(fig)
    x=pd.read_csv(OUT/'synthetic_duration_frequency_plans.csv')
    x['weighted_response']=x.synthetic_incremental_conversions_per_10000*x.audience_share
    x['weighted_contacts']=x.mean_recorded_contacts*x.audience_share
    w=x.groupby(['day','contact_cap'])[['weighted_response','weighted_contacts']].sum().reset_index()
    ref=w.query('day==14 and contact_cap==400').iloc[0]
    w['relative_response_pct']=100*w.weighted_response/ref.weighted_response
    w['relative_contacts_pct']=100*w.weighted_contacts/ref.weighted_contacts
    w.to_csv(OUT/'uniform_plan_comparison.csv',index=False)
    # Calendar scenario: distribute fictional entrants across observed campaign
    # arrival days, then truncate each person's contact window at campaign end.
    # Responses may arrive afterward, within that person's 14-day label horizon.
    reach28=pd.DataFrame(reach).query('horizon==28').sort_values('day')
    arrivals=np.diff(np.r_[0,reach28.share_reached.to_numpy()])
    calendar=[]
    for run_days in range(1,29):
        for cap in [1,2,3,4,5,6,8,10,15,20,400]:
            response=0.;load=0.
            for arrival_day in range(1,run_days+1):
                followup=min(14,run_days-arrival_day+1)
                a=w[(w.day==followup)&(w.contact_cap==cap)].iloc[0]
                response+=arrivals[arrival_day-1]*a.weighted_response
                load+=arrivals[arrival_day-1]*a.weighted_contacts
            calendar.append(dict(campaign_days=run_days,contact_cap=cap,share_of_28d_potential_audience_reached=float(reach28.loc[reach28.day.eq(run_days),'share_reached'].iloc[0]),synthetic_eventual_incremental_conversions_per_100000=10*response,synthetic_recorded_contacts_per_100000=100000*load,endpoint='Eventual response within each entrant 14-day horizon, including response after campaign ends',assumptions='Common arrival distribution across synthetic groups; arrivals at start of each day; no contacts after campaign ends; full-path retention model'))
    calendar_table=pd.DataFrame(calendar)
    calendar_table.to_csv(OUT/'campaign_calendar_plans.csv',index=False)
    for _,a in calendar_table.groupby('contact_cap'):
        assert np.all(np.diff(a.sort_values('campaign_days').synthetic_eventual_incremental_conversions_per_100000)>=-1e-10)
        assert np.all(np.diff(a.sort_values('campaign_days').synthetic_recorded_contacts_per_100000)>=-1e-10)
    choices=w[w.day.isin([1,7,10,14])&w.contact_cap.isin([1,3,5,8,400])]
    choices.to_csv(OUT/'shortlisted_plans.csv',index=False)
    fig,axes=plt.subplots(1,2,figsize=(13.2,5.6))
    caps=[1,2,3,4,5,6,8,10]
    heat=w[w.contact_cap.isin(caps)].pivot(index='contact_cap',columns='day',values='relative_response_pct').reindex(caps)
    im=axes[0].imshow(heat.to_numpy(),origin='lower',aspect='auto',cmap='Blues',vmin=45,vmax=100)
    axes[0].set_xticks(np.arange(14),np.arange(1,15));axes[0].set_yticks(np.arange(8),caps)
    axes[0].set(xlabel='Days allowing recorded contacts',ylabel='Per-history contact cap',title='Synthetic response retained (%)')
    for rr in range(8):
        for cc in range(14):
            val=heat.iloc[rr,cc]
            if cc in [0,2,6,9,13]:axes[0].text(cc,rr,f'{val:.0f}',ha='center',va='center',color='white' if val>78 else '#172b4d',fontsize=9)
    fig.colorbar(im,ax=axes[0],fraction=.025,pad=.03)
    chosen=[(14,1),(7,5),(10,5),(14,400)]
    for d,k in chosen:
        a=w[(w.day==d)&(w.contact_cap==k)].iloc[0]
        label=f'{d} days / '+('uncapped' if k==400 else f'{k} contacts')
        axes[1].scatter(a.relative_contacts_pct,a.relative_response_pct,s=65,color='#2563eb')
        offset={ (14,1):(8,-4),(7,5):(-110,-20),(10,5):(-65,13),(14,400):(-105,-3)}[(d,k)]
        axes[1].annotate(label,(a.relative_contacts_pct,a.relative_response_pct),xytext=offset,textcoords='offset points',fontsize=10)
    axes[1].set(xlabel='Recorded contact load vs 14-day uncapped plan (%)',ylabel='Synthetic incremental response retained (%)',xlim=(45,105),ylim=(45,105),title='The decision: more response or fewer contacts?')
    style(axes[1])
    fig.suptitle('A prototype duration-and-frequency planning scenario',fontsize=16,x=.025,ha='left',y=.98)
    fig.text(.025,.025,'Synthetic propensity-rank bridge + full-path replay assumption. Response retention is modeled; observed contacts are a load proxy, not actual spend.',fontsize=10,color='#475569')
    fig.tight_layout(rect=[0,.065,1,.92]);fig.savefig(OUT/'planning_scenario.png',dpi=170,bbox_inches='tight');plt.close(fig)
    c=pd.read_csv(OUT/'synthetic_duration_scenario.csv')
    fig,ax=plt.subplots(figsize=(9,5.5))
    for s,color in [(1,'#2563eb'),(2,'#7c3aed'),(4,'#0f766e')]:
        a=c[c.synthetic_segment_id==s];ax.plot(a.day,100*a.attribution_response_share,lw=2.5,label=a.synthetic_label.iloc[0],color=color)
    ax.set(xlabel='Days since first recorded contact',ylabel='Share of each profile’s 14-day responses (%)',xlim=(1,14),ylim=(30,103),title='Synthetic audience profiles inherit different empirical timing shapes')
    ax.legend(frameon=False,loc='lower right');style(ax)
    fig.text(.025,.02,'Curve shapes from propensity-matched held-out histories; synthetic labels and cross-source matching.',fontsize=9,color='#475569')
    fig.tight_layout(rect=[0,.06,1,1]);fig.savefig(OUT/'matched_profile_shapes.png',dpi=170,bbox_inches='tight');plt.close(fig)
    assert np.all(np.diff(curves.response_observed_pct)>=0)
    for _,a in x.groupby(['synthetic_segment_id','contact_cap']):assert np.all(np.diff(a.sort_values('day').historical_path_coverage)>=-1e-12)
    for _,a in x.groupby(['synthetic_segment_id','day']):assert np.all(np.diff(a.sort_values('contact_cap').historical_path_coverage)>=-1e-12)
    assert np.isclose(w.query('day==14 and contact_cap==400').relative_response_pct.iloc[0],100)
    checks=dict(equal_followup_histories=4941310,event_histories=len(e),duration_and_cap_monotonic=True,baseline_reconciliation=True,plan_rows=len(x),calendar_plan_rows=len(calendar),bridge_is_synthetic=True,stopping_effect_is_modeled=True)
    (OUT/'review_validation.json').write_text(json.dumps(checks,indent=2))
    print(choices.round(3).to_string(index=False))

if __name__=='__main__':main()
