from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'outputs/feature_exploration'
p=pd.read_csv(out/'feature_profile.csv')
a=pd.read_csv(out/'conversion_concentration_ablations.csv')
fig,axes=plt.subplots(1,2,figsize=(12,5),layout='constrained')
p=p.sort_values('directional_conversion_auc')
axes[0].barh(p.feature,p.directional_conversion_auc,color=['#087F8C' if x=='f8' else '#819A9E' for x in p.feature])
axes[0].set_xlim(.5,1)
axes[0].set_xlabel('Single-feature conversion AUC (estimation users)')
axes[0].set_title('f8 is strongly associated with conversion')
labels={'all_features':'All features','without_f8':'Remove f8','without_f2_f8':'Remove f2 + f8',
        'without_f2_f8_f9':'Remove f2 + f8 + f9','clip_0.1_99.9_pct':'Clip extreme 0.1% tails'}
for name,frame in a.groupby('variant',sort=False):
 axes[1].plot(frame.clusters,frame.treatment_conversion_capture_pct,marker='o',label=labels[name])
axes[1].set_xscale('log',base=2)
axes[1].set_xticks([2,4,8,16,32,64],labels=['2','4','8','16','32','64'])
axes[1].set_ylim(0,105)
axes[1].set_xlabel('Number of balanced feature clusters')
axes[1].set_ylabel('Treatment conversions in selected cluster (%)')
axes[1].set_title('Concentration changes when f8 is removed')
axes[1].legend(fontsize=8,loc='lower left')
for axis in axes:
 axis.spines[['top','right']].set_visible(False)
 axis.grid(axis='y',alpha=.15)
fig.suptitle('Feature sensitivity checks — all customers retained',fontsize=15)
fig.savefig(out/'feature_sensitivity.png',dpi=170)
plt.close(fig)
