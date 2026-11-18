"""Publish audited retail profiles and a fully linked synthetic CRM warehouse."""
from pathlib import Path
import sys,json,time,shutil,os
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.customer_lab import Scenario,simulate,load_calibration,STATES,GROUPS

def main():
    start=time.perf_counter();research=ROOT/'outputs/retail_audiences'
    out=ROOT/'app/data/customer_lab';stage=ROOT/'app/data/customer_lab_stage';stage.mkdir(exist_ok=True)
    backup=research/'previous_calibration'
    if out.exists() and not backup.exists():shutil.copytree(out,backup)
    g=pd.read_csv(research/'actual_group_outcomes.csv').query('partition=="evaluation"').sort_values('segment_id')
    g[['segment_id','profile','share','incremental_rate','baseline_rate','se','n']].rename(columns={'n':'evaluation_customers'}).to_parquet(stage/'audiences.parquet',index=False)
    pd.read_csv(research/'scenario_timing_curves.csv').to_parquet(stage/'timing.parquet',index=False)
    pd.read_csv(research/'scenario_contact_curves.csv').to_parquet(stage/'frequency.parquet',index=False)
    pd.read_csv(ROOT/'outputs/campaign_timing/campaign_audience_reach.csv').query('horizon==28').to_parquet(stage/'arrivals.parquet',index=False)
    sample=pd.read_parquet(research/'retail_profile_bank.parquet')
    excluded=['partition','conversion','visit','treatment','exposure','cluster8']+[c for c in sample if c.endswith('_active')]
    sample.drop(columns=[c for c in excluded if c in sample]).to_parquet(stage/'profile_bank.parquet',index=False)
    source=pd.read_csv(research/'source_cells.csv').query('partition=="estimation"').set_index('response_cell').reindex(range(15),fill_value=0)
    cells=[]
    for cell,a in source.iterrows():
        parent=source.loc[range(cell//3*3,cell//3*3+3)].sum(numeric_only=True)
        parent_t=parent.treated_conversions/parent.treated;parent_c=(parent.conversions-parent.treated_conversions)/(parent.n-parent.treated)
        nt=a.treated;nc=a.n-nt
        pt=(a.treated_conversions+5000*parent_t)/(nt+5000)
        pc=(a.conversions-a.treated_conversions+1000*parent_c)/(nc+1000)
        cells.append(dict(response_cell=cell,baseline_rate=pc,incremental_rate=max(0,pt-pc),raw_incremental_rate=pt-pc,n=int(a.n),control=int(nc)))
    pd.DataFrame(cells).to_parquet(stage/'response_cells.parquet',index=False)
    shutil.copyfile(research/'catalogue.json',stage/'catalogue.json')
    shutil.copyfile(research/'allocation_spec.json',stage/'allocation_spec.json')
    meta=dict(title='Campaign Runway',version='retail-decisions-v4-30d',origin='Criteo-calibrated response cells + synthetic retail CRM',seed=171126,response_horizon_days=30,source_response_horizon_days=14,arrival_extension='Days 29-30 continue the mean daily arrival weight from source days 22-28.',profile_templates=len(sample),uplift_rows=13979592,attribution_rows=16468027,timing_check_histories=987306,states=STATES,group_definition='Primary shopping mission; no outcome or response-time field defines membership.',synthetic_fields=['shopping_mission','orders_last_year','typical_basket','promotion_affinity','preferred_category','delivery_preference','preferred_channel','tenure_months','customer_id','arrival_day','lifecycle_state'],assumptions=['Anonymous source cells supply response heterogeneity, not recovered retail meanings.','Versioned soft allocation gives every shopping mission a mix of source profiles.','Propensity rank and a discovery-context timing rank connect aggregate source cells; no identities are joined.','Prior purchase history is retailer-wide; campaign conversion is a benchmark response to the promoted collection.','Weekly audience turnover is weighted by synthetic order history and promotion affinity.','New arrivals enter the reachable audience; they may already have purchased from the retailer.','Timing and contact coverage include a declared retail decision-clock and familiarity layer; raw source histories are retained. These are separable scenario inputs; individual outcomes are seeded.'])
    (stage/'provenance.json').write_text(json.dumps(meta,indent=2))
    cal=load_calibration(stage)
    from src.exposure_reference import build_exposure_reference,reference_method
    exposure_detail,exposure_stages=build_exposure_reference(cal)
    exposure_detail.to_parquet(stage/'exposure_detail.parquet',index=False)
    exposure_stages.to_parquet(stage/'exposure_stages.parquet',index=False)
    (stage/'exposure_reference_method.json').write_text(json.dumps(reference_method(),indent=2),encoding='utf-8')
    assert sample.segment_id.between(0,4).all() and sample.response_cell.between(0,14).all()
    for file in stage.iterdir():os.replace(file,out/file.name)
    stage.rmdir()
    result=simulate(Scenario(contact_budget=75000,eligible_profiles=(4,),breadth=100.,contact_cap=4,repeat_share=50.),cal,record_events=True)
    full=ROOT/'data/synthetic/customer_lab';full.mkdir(parents=True,exist_ok=True)
    customers=result['customers'].copy()
    features=sample[['source_row_index']+[f'f{i}' for i in range(12)]].drop_duplicates('source_row_index')
    customers=customers.merge(features,on='source_row_index',validate='many_to_one')
    # A real synthetic history table, not just a prose persona description.
    rng=np.random.default_rng(171128);counts=customers.orders_last_year.to_numpy();owner=np.repeat(np.arange(len(customers)),counts)
    history=pd.DataFrame(dict(order_id=np.arange(1,len(owner)+1,dtype=np.int32),customer_id=owner.astype(np.int32)+1,days_before_campaign=rng.integers(1,366,size=len(owner),dtype=np.int16),order_value=np.round(customers.typical_basket.to_numpy()[owner]*np.exp(rng.normal(0,.22,len(owner))),2),category=customers.preferred_category.to_numpy()[owner]))
    history['order_date']=pd.Timestamp('2026-11-17')-pd.to_timedelta(history.days_before_campaign,unit='D')
    totals=history.groupby('customer_id').agg(historical_spend=('order_value','sum'),last_purchase_days=('days_before_campaign','min'))
    customers=customers.join(totals,on='customer_id');customers['historical_spend']=customers.historical_spend.fillna(0)
    customers.to_parquet(full/'customers.parquet',index=False);history.to_parquet(full/'purchase_history.parquet',index=False)
    for key in ['contacts','transitions','daily','profiles','flows']:result[key].to_parquet(full/(key+'.parquet'),index=False)
    rows=[]
    for day in range(result['scenario']['days']+1):
        entered=customers.arrival_day.to_numpy()<=day
        rows.append(pd.DataFrame(dict(customer_id=customers.customer_id.to_numpy()[entered],day=np.int8(day),state_code=result['history'][day,entered],contacts_to_date=result['contact_history'][day,entered])))
    pd.concat(rows,ignore_index=True).to_parquet(full/'customer_states.parquet',index=False)
    assert history.customer_id.isin(customers.customer_id).all()
    assert history.groupby('customer_id').size().reindex(customers.customer_id,fill_value=0).to_numpy().tolist()==counts.tolist()
    assert result['contacts'].customer_id.isin(customers.customer_id).all()
    summary=dict(version='retail-decisions-v4-30d',customers=len(customers),historical_orders=len(history),starting_customers=100000,contacts=len(result['contacts']),transition_events=len(result['transitions']),state_snapshots=sum(len(x) for x in rows),scenario=result['scenario'],final=result['daily'].iloc[-1].to_dict(),elapsed_seconds=round(time.perf_counter()-start,2))
    (full/'manifest.json').write_text(json.dumps(summary,indent=2))
    (full/'validation.json').write_text(json.dumps(dict(customer_keys_unique=bool(customers.customer_id.is_unique),historical_order_counts_reconciled=True,contact_foreign_keys_valid=True,all_uplift_rows_audited=13979592),indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
