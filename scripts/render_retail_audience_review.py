"""Render the construction audit as shareable scientific figures."""
from pathlib import Path
import json,os
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'outputs/retail_audiences'
os.environ.setdefault('MPLCONFIGDIR',str(OUT/'matplotlib_cache'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def style(ax):
    ax.spines[['top','right']].set_visible(False);ax.grid(axis='x',color='#e6ecea');ax.set_axisbelow(True)
    ax.tick_params(length=0,pad=7)

def main():
    cat=pd.read_json(OUT/'catalogue.json');names=cat.profile.tolist();yy=np.arange(5)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.color':'#18383d','axes.labelcolor':'#345158','figure.facecolor':'white','axes.facecolor':'white'})
    fig,axes=plt.subplots(1,3,figsize=(14,5.1),sharey=True)
    for ax,col,title,color in zip(axes,['orders_median','basket_median','promotion_affinity'],['Orders in the past year (median)','Typical basket ($, median)','Promotion preference (%)'],['#087f8c','#b38350','#6874b8']):
        values=cat[col].to_numpy()*(100 if col=='promotion_affinity' else 1)
        ax.barh(yy,values,height=.5,color=color)
        for i,v in enumerate(values):ax.text(v+max(values)*.03,i,f'{v:.0f}',va='center')
        ax.set_xlim(0,max(values)*1.2);ax.set_title(title,pad=16);style(ax)
    axes[0].set_yticks(yy,names);axes[0].invert_yaxis()
    fig.suptitle('Meet the customers: five retail missions with explicit CRM attributes',x=.02,ha='left',fontsize=16)
    fig.text(.02,.02,'Synthetic retail fields from a reproducible 200,000-template customer bank. Customer group is defined by shopping mission, not response timing.',fontsize=10,color='#526b70')
    fig.tight_layout(rect=[0,.07,1,.91]);fig.savefig(OUT/'customer_fingerprints.png',dpi=165,bbox_inches='tight');plt.close(fig)
    curves=pd.read_csv(OUT/'mission_timing_curves.csv').query('partition=="check"')
    freq=pd.read_csv(OUT/'mission_contact_curves.csv').query('partition=="check" and contact_cap<=12')
    colors=['#64748b','#16859a','#6874c5','#bc7541','#276b50']
    fig,axes=plt.subplots(1,2,figsize=(13,5.5))
    for gid,name in enumerate(names):
        a=curves[curves.segment_id==gid];b=freq[freq.segment_id==gid]
        axes[0].plot(a.day,100*a.response_share,label=name,color=colors[gid],lw=2.3)
        axes[1].plot(b.contact_cap,100*b.coverage,label=name,color=colors[gid],lw=2.3)
    axes[0].set(xlabel='Days after first recorded contact',ylabel='Share of 14-day response histories (%)',ylim=(25,102),xlim=(1,14),title='Response timing becomes a finding about the customer')
    axes[1].set(xlabel='Recorded contacts before response',ylabel='Historical response paths covered (%)',ylim=(25,102),xlim=(1,12),title='Contact patterns also differ')
    for ax in axes:style(ax)
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False,bbox_to_anchor=(.55,.01))
    fig.suptitle('Held-out source histories, assigned through the synthetic mission bridge',x=.02,ha='left',fontsize=15)
    fig.tight_layout(rect=[0,.15,1,.92]);fig.savefig(OUT/'retail_response_curves.png',dpi=165,bbox_inches='tight');plt.close(fig)
    stress=pd.read_csv(OUT/'campaign_stress_summary.csv')
    worlds=['Tight contact budget','Default','Larger contact budget','High contact budget'];labels=['30,000 contacts','75,000 contacts','150,000 contacts','250,000 contacts']
    fig,ax=plt.subplots(figsize=(10,5))
    for j,(policy,color) in enumerate([('Focused','#087f8c'),('Wide reach','#c78450')]):
        a=stress[stress.policy==policy].set_index('world').loc[worlds]
        x=np.arange(4)+(j-.5)*.24
        ax.bar(x,a.responses_mean,width=.24,color=color,label=policy)
        ax.errorbar(x,a.responses_mean,yerr=[a.responses_mean-a.responses_min,a.responses_max-a.responses_mean],fmt='none',color='#344f57',capsize=4)
    ax.set_xticks(range(4),labels);ax.set_ylabel('Modeled ad-driven responses');ax.set_title('The same audience can favor different policies at different budgets',pad=16)
    ax.legend(frameon=False);style(ax)
    fig.text(.02,.02,'Mean and min/max across three fixed seeds. Focus: convenience shoppers, cap 4, repeat preference 50%. Wide: all missions, cap 3, repeat 20%. Synthetic outcomes.',fontsize=9,color='#526b70')
    fig.tight_layout(rect=[0,.07,1,1]);fig.savefig(OUT/'budget_tradeoff.png',dpi=165,bbox_inches='tight');plt.close(fig)
    timing=pd.read_csv(OUT/'mission_timing_checks.csv')
    pivot=timing.pivot(index='segment_id',columns='partition',values='day1_share')
    checks=dict(all_uplift_rows_audited=13979592,heldout_histories=int(timing.query('partition=="check"').n.sum()),heldout_responding_histories=int(timing.query('partition=="check"').events14.sum()),allocation_candidates=14,max_day1_share_discovery_check_difference=float((pivot.discovery-pivot['check']).abs().max()),policy_stress_runs=42,policy_probe_runs=24,baseline_mixed_focus_stress_runs=36)
    (OUT/'review_validation.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks,indent=2))

if __name__=='__main__':main()
