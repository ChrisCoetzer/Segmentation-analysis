"""Stress-test the new retail groups without selecting a predetermined winner."""
from pathlib import Path
from dataclasses import replace
import sys
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.customer_lab import Scenario,simulate,load_calibration

def main():
    cal=load_calibration(ROOT/'app/data/customer_lab');out=ROOT/'outputs/retail_audiences'
    worlds=[('Default',75000,10,15),('Tight contact budget',30000,10,15),('Larger contact budget',150000,10,15),('High contact budget',250000,10,15),('High turnover',75000,35,15),('No arrivals',75000,10,0),('Many arrivals',75000,10,30)]
    rows=[]
    for world,budget,turnover,arrivals in worlds:
        for seed in [171126,171127,171128]:
            base=Scenario(contact_budget=budget,weekly_turnover=turnover,weekly_arrivals=arrivals,seed=seed,breadth=100.)
            policies={'Focused':replace(base,eligible_profiles=(4,),contact_cap=4,repeat_share=50.),'Wide reach':replace(base,eligible_profiles=tuple(range(5)),contact_cap=3,repeat_share=20.)}
            for label,s in policies.items():
                r=simulate(s,cal);d=r['daily'].iloc[-1]
                rows.append(dict(world=world,seed=seed,policy=label,responses=int(d.ad_responses),reach=int(d.unique_reached),contacts=int(d.cumulative_contacts),day7_responses=int(r['daily'].iloc[6].ad_responses),day14_responses=int(r['daily'].iloc[13].ad_responses),inactive=int(d.inactive),budget=budget))
        print('Completed',world,flush=True)
    frame=pd.DataFrame(rows);frame.to_csv(out/'campaign_stress_checks.csv',index=False)
    summary=frame.groupby(['world','policy']).agg(responses_mean=('responses','mean'),responses_min=('responses','min'),responses_max=('responses','max'),reach=('reach','mean'),contacts=('contacts','mean'),day7_responses=('day7_responses','mean')).reset_index()
    summary.to_csv(out/'campaign_stress_summary.csv',index=False)
    print(summary.round(1).to_string(index=False),flush=True)

if __name__=='__main__':main()
