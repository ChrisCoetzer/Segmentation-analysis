"""Build explicit retail decision scenarios, preserving raw held-out histories.

The source does not reveal retail missions. A monotone 30-day decision clock
and synthetic familiarity requirement are declared metadata assumptions, not
newly discovered effects. Compare multiple strengths before publishing.
"""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.retail_metadata import decision_metadata,GROUPS,PACE_EXPONENT,FAMILIARITY_PROB,FAMILIARITY_EXTRA,identify_missions

def main():
    out=ROOT/'outputs/retail_audiences'
    raw=pd.read_parquet(out/'heldout_timing_missions.parquet')
    ids=pd.util.hash_pandas_object(raw[['uid','campaign']],index=False).to_numpy()
    raw=raw.copy();raw['lineage_hash']=ids
    candidates=[];curves=[];frequency=[];summaries=[]
    for strength in [0.,.5,.75,1.]:
        pace,extra=decision_metadata(raw.segment_id,ids,strength)
        # Map the source's 14-day follow-up to a declared 30-day retail clock.
        # This is scenario construction, not newly observed 30-day follow-up.
        days=30*np.power(np.clip(raw.event_days.to_numpy()/14,0,1),pace)
        contacts=raw.event_contact_number.to_numpy()+extra
        for gid in range(5):
            mask=raw.segment_id.eq(gid)&raw.event14
            d=days[mask];n=contacts[mask]
            row=dict(strength=strength,segment_id=gid,profile=GROUPS[gid],source_events14=len(d),scenario_events30=len(d),day1_share=float(np.mean(d<=1)),day3_share=float(np.mean(d<=3)),day7_share=float(np.mean(d<=7)),median_days=float(np.median(d)),one_contact=float(np.mean(n<=1)),cap3_share=float(np.mean(n<=3)))
            candidates.append(row)
            if strength==1.:
                summaries.append(row)
                for day in range(1,31):curves.append(dict(segment_id=gid,day=day,response_share=float(np.mean(d<=day)),n_histories=int(raw.segment_id.eq(gid).sum()),source_events14=len(d),scenario_events30=len(d)))
                for cap in [1,2,3,4,5,6,8,10,12,15,20,400]:frequency.append(dict(segment_id=gid,contact_cap=cap,coverage=float(np.mean(n<=cap)),source_events14=len(d),scenario_events30=len(d)))
        if strength==1.:
            raw['scenario_event_days']=days;raw['scenario_event_contact_number']=contacts
            raw['decision_pace_exponent']=pace;raw['familiarity_extra_contacts']=extra
    audit=pd.DataFrame(candidates);audit.to_csv(out/'response_scenario_candidates.csv',index=False)
    pd.DataFrame(curves).to_csv(out/'scenario_timing_curves.csv',index=False)
    pd.DataFrame(frequency).to_csv(out/'scenario_contact_curves.csv',index=False)
    summary=pd.DataFrame(summaries);summary.to_csv(out/'scenario_response_summary.csv',index=False)
    raw.to_parquet(out/'scenario_timing_missions.parquet',index=False)
    bank=pd.read_parquet(out/'retail_profile_bank.parquet')
    bank['decision_pace_exponent'],bank['familiarity_extra_contacts']=decision_metadata(bank.segment_id,bank.source_row_index)
    assert np.array_equal(identify_missions(bank),bank.segment_id)
    bank.to_parquet(out/'retail_profile_bank.parquet',index=False)
    spec=json.loads((out/'allocation_spec.json').read_text())
    spec['retail_decision_layer']=dict(version='retail-decisions-v4-30d',source_horizon_days=14,scenario_horizon_days=30,selected_strength=1.,tested_strengths=[0.,.5,.75,1.],pace_exponents=PACE_EXPONENT.tolist(),extra_contact_probability=FAMILIARITY_PROB.tolist(),extra_contact_count=FAMILIARITY_EXTRA.tolist(),time_transform='scenario_day = 30 * (source_day / 14) ** mission_exponent',contact_transform='scenario_contacts = source_contacts + deterministic synthetic familiarity requirement',interpretation='Explicit synthetic 30-day decision clock applied to 14-day held-out source histories. Not observed 30-day follow-up, observed retail segment behavior or causal ad effects. Raw source curves retained.')
    (out/'allocation_spec.json').write_text(json.dumps(spec,indent=2))
    assert summary.day1_share.max()-summary.day1_share.min()>.4
    assert summary.cap3_share.max()-summary.cap3_share.min()>.25
    print(audit.round(3).to_string(index=False))

if __name__=='__main__':main()
