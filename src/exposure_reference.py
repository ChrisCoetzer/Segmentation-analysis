"""Fixed-cohort exposure analysis, separate from configurable campaign playback.

The benchmark incremental rate is the response potential. Frequency coverage
allocates it across exposures. Every not-yet-responded customer receives the
next exposure, including those who never respond. This is an explicit reference
calculation, not an estimate of causal marginal ad effects.
"""
import numpy as np
import pandas as pd

STAGES=[(1,1,'1st'),(2,2,'2nd'),(3,4,'3rd–4th'),(5,8,'5th–8th'),(9,12,'9th–12th')]
REFERENCE_CUSTOMERS=100000

def build_exposure_reference(cal,customers=REFERENCE_CUSTOMERS):
    rows=[]
    for _,group in cal['groups'].sort_values('segment_id').iterrows():
        gid=int(group.segment_id)
        frequency=cal['frequency'].query('segment_id==@gid').sort_values('contact_cap')
        coverage=np.interp(np.arange(13),np.r_[0,frequency.contact_cap],np.r_[0,frequency.coverage])
        lift=max(0,float(group.incremental_rate))
        probability=lift*coverage
        cumulative_contacts=0.
        for exposure in range(1,13):
            contacts=customers*(1-probability[exposure-1])
            additional=customers*(probability[exposure]-probability[exposure-1])
            cumulative_contacts+=contacts
            rows.append(dict(segment_id=gid,profile=group.profile,exposure=exposure,customers=customers,response_potential=customers*lift,coverage=float(coverage[exposure]),additional_responses=additional,cumulative_responses=customers*probability[exposure],contacts=contacts,cumulative_contacts=cumulative_contacts,responses_per_1000_contacts=1000*additional/contacts))
    detailed=pd.DataFrame(rows);stages=[]
    for (gid,profile),a in detailed.groupby(['segment_id','profile']):
        for stage_id,(first,last,label) in enumerate(STAGES):
            b=a[a.exposure.between(first,last)];end=b.iloc[-1]
            contacts=float(b.contacts.sum());responses=float(b.additional_responses.sum())
            stages.append(dict(segment_id=gid,profile=profile,stage_id=stage_id,stage=label,first_exposure=first,last_exposure=last,customers=customers,additional_responses=responses,contacts=contacts,responses_per_1000_contacts=1000*responses/contacts,cumulative_responses=float(end.cumulative_responses),coverage=float(end.coverage),response_potential=float(end.response_potential)))
    return detailed,pd.DataFrame(stages)

def reference_method():
    return dict(version='exposure-reference-v1',customers_per_group=REFERENCE_CUSTOMERS,horizon_days=30,maximum_exposures=12,response='benchmark incremental conversion rate * cumulative exposure coverage',additional_responses='population * incremental rate * change in exposure coverage',contacts='population minus expected advertising-associated responders from preceding exposures',cost_basis='All not-yet-responded customers receive each next exposure, including eventual nonresponders.',time_basis='Thirty-day response potential held fixed to isolate exposure count. Exposures are not days.',scope='Fixed reference cohort: no arrivals, turnover, organic purchase simulation, targeting optimization or budget constraint. The Phase 2 simulation adds campaign scheduling and environment.',interpretation='Criteo-calibrated synthetic reference expectations, not measured marginal causal ad effects.')
