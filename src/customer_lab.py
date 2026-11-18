"""Seeded customer stock/flow simulation, calibrated to prepared Criteo summaries.

Profiles are static; lifecycle states change. Individual potential outcomes,
turnover, returning customers and state transitions are synthetic assumptions.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
import pandas as pd
from src.retail_metadata import GROUPS

STATES=['New','Engaged','Ready','Responded','Inactive','Returning','Not arrived']
COLORS=['#9fb2cb','#69d1df','#b0a4ff','#efb078','#79d4a7']
SIMULATION_VERSION='selected-population-first-ad-v3-organic20'

@dataclass(frozen=True)
class Scenario:
    population: int=100000
    days: int=30
    contact_budget: int=150000
    breadth: float=25.
    contact_cap: int=6
    repeat_share: float=65.
    weekly_arrivals: float=15.
    weekly_turnover: float=10.
    weekly_return: float=8.
    seed: int=171126
    eligible_profiles: tuple[int,...] | None=None
    # Shared population for a comparison; advertising eligibility is separate.
    population_profiles: tuple[int,...] | None=None
    organic_rate_scale: float=.20

def load_calibration(path):
    path=Path(path)
    result=dict(groups=pd.read_parquet(path/'audiences.parquet'),
                shapes=pd.read_parquet(path/'timing.parquet'),
                frequency=pd.read_parquet(path/'frequency.parquet'),
                arrivals=pd.read_parquet(path/'arrivals.parquet'),
                templates=pd.read_parquet(path/'profile_bank.parquet'))
    if (path/'response_cells.parquet').exists():result['response_cells']=pd.read_parquet(path/'response_cells.parquet')
    for key,file in [('exposure_detail','exposure_detail.parquet'),('exposure_stages','exposure_stages.parquet')]:
        if (path/file).exists():result[key]=pd.read_parquet(path/file)
    if (path/'catalogue.json').exists():
        import json
        result['catalogue']=json.loads((path/'catalogue.json').read_text())
    return result

def make_population(s,calibration):
    arrivals=calibration['arrivals'].sort_values('day').share_reached.to_numpy()
    weights=np.diff(np.r_[0,arrivals])
    if s.days>len(weights):
        # Source reach shape has 28 days; continue its last-week mean flow.
        weights=np.r_[weights,np.full(s.days-len(weights),weights[-7:].mean())]
    weights=weights[:s.days]
    weights=weights/weights.sum()
    total_new=round(s.population*s.weekly_arrivals/100*s.days/7)
    daily=np.diff(np.r_[0,np.round(np.cumsum(weights)*total_new)]).astype(int)
    cohort=np.r_[np.zeros(s.population,dtype=int),np.repeat(np.arange(1,s.days+1),daily)]
    n=len(cohort)
    bank=calibration['templates']
    rng=np.random.default_rng(s.seed)
    allowed=tuple(sorted(set(s.population_profiles))) if s.population_profiles is not None else tuple(range(len(GROUPS)))
    if not allowed or any(g not in range(len(GROUPS)) for g in allowed):
        raise ValueError('Choose at least one valid group for the shared population')
    shares=calibration['groups'].set_index('segment_id').loc[list(allowed),'share'].to_numpy(dtype=float)
    if np.any(shares<=0):raise ValueError('Selected population groups must have positive shares')
    shares=shares/shares.sum()
    def cohort_groups(size):
        exact=size*shares;counts=np.floor(exact).astype(int)
        counts[np.argsort(-(exact-counts),kind='stable')[:size-counts.sum()]]+=1
        return rng.permutation(np.repeat(np.asarray(allowed),counts))
    # Preserve the conditional population proportions separately for the initial
    # cohort and arrivals, to within one customer, rather than resampling shares.
    population_group=np.r_[cohort_groups(s.population),cohort_groups(total_new)]
    ix=np.empty(n,dtype=np.int64)
    for gid in allowed:
        rows=np.flatnonzero(population_group==gid)
        templates=np.flatnonzero(bank.segment_id.to_numpy()==gid)
        if not len(templates):raise ValueError(f'No templates available for group {gid}')
        ix[rows]=rng.choice(templates,size=len(rows),replace=True)
    # Sampling within each group retains its customer heterogeneity. Every
    # generated customer has a new ID; templates are not recovered identities.
    columns=['source_row_index','segment_id','engagement_style','shopping_need','message_theme','response_cell','shopping_mission','orders_last_year','typical_basket','promotion_affinity','preferred_category','delivery_preference','preferred_channel','customer_relationship','tenure_months','metadata_origin','decision_pace_exponent','familiarity_extra_contacts']
    customers=bank.iloc[ix][[c for c in columns if c in bank]].reset_index(drop=True)
    customers.insert(0,'customer_id',np.arange(1,n+1,dtype=np.int32))
    customers['arrival_day']=cohort.astype(np.int16)
    customers['cohort']=np.where(cohort==0,'Starting audience','Week '+np.maximum(1,np.ceil(cohort/7).astype(int)).astype(str))
    customers['synthetic_origin']='Synthetic customer; Criteo-derived profile template'
    return customers

def simulate(s,calibration,record_events=False):
    if s.population<=0 or not 1<=s.days<=30 or s.contact_budget<0:
        raise ValueError('Positive population, 1–30 days, and nonnegative contact budget required')
    if not 0<s.breadth<=100 or s.contact_cap<1:
        raise ValueError('A positive breadth and contact cap are required')
    if not 0<=s.organic_rate_scale<=1:
        raise ValueError('Organic response scale must be between 0 and 1')
    customers=make_population(s,calibration)
    n=len(customers);group=customers.segment_id.to_numpy(dtype=int)
    cohort=customers.arrival_day.to_numpy(dtype=int)
    g=calibration['groups'].sort_values('segment_id')
    if 'response_cells' in calibration and 'response_cell' in customers:
        rates=calibration['response_cells'].sort_values('response_cell');cells=customers.response_cell.to_numpy(dtype=int)
        lift=rates.incremental_rate.to_numpy()[cells]
        baseline=rates.baseline_rate.to_numpy()[cells]
        readiness=cells//3
    else:
        lift=g.incremental_rate.to_numpy()[group]
        baseline=g.baseline_rate.to_numpy()[group]
        readiness=group
    # Shared scenario adjustment to baseline purchases, not advertising uplift.
    baseline=baseline*s.organic_rate_scale
    response_horizon=int(calibration['shapes'].day.max())
    cdf=np.zeros((5,response_horizon+1))
    frequency=np.zeros((5,s.contact_cap+1))
    for k in range(5):
        a=calibration['shapes'].query('segment_id==@k').sort_values('day')
        cdf[k,1:]=np.interp(np.arange(1,response_horizon+1),a.day,a.response_share)
        b=calibration['frequency'].query('segment_id==@k').sort_values('contact_cap')
        frequency[k]=np.interp(np.arange(s.contact_cap+1),np.r_[0,b.contact_cap],np.r_[0,b.coverage])
    rng=np.random.default_rng(s.seed+1)
    organic_threshold=rng.random(n);ad_threshold=rng.random(n)
    initial=rng.random(n)
    engaged=np.array([.15,.45,.65,.35,.20])[readiness]
    ready=np.array([.01,.05,.18,.60,.78])[readiness]
    state=np.where(initial<ready,2,np.where(initial<ready+engaged,1,0)).astype(np.int8)
    state[cohort>0]=6
    # New entrants begin as New, regardless of their propensity profile.
    contacts=np.zeros(n,dtype=np.int16)
    first_contact_day=np.full(n,-1,dtype=np.int16)
    ad_response_day=np.full(n,-1,dtype=np.int16)
    organic_response_day=np.full(n,-1,dtype=np.int16)
    touched=np.zeros(n,dtype=bool);ad_responded=np.zeros(n,dtype=bool)
    organic_responded=np.zeros(n,dtype=bool)
    history=np.empty((s.days+1,n),dtype=np.int8);history[0]=state
    contact_history=np.zeros((s.days+1,n),dtype=np.int16)
    daily=[];flows=[];events=[];transitions=[]
    if 'orders_last_year' in customers:
        # A disclosed synthetic retention assumption, not a Criteo estimate.
        loyalty=1/np.sqrt(1+customers.orders_last_year.to_numpy()/4)
        loyalty*=1+.4*customers.promotion_affinity.to_numpy()
        loyalty/=loyalty.mean()
    else:loyalty=np.ones(n)
    day_exit=1-(1-s.weekly_turnover/100)**(loyalty/7)
    day_return=1-(1-s.weekly_return/100)**(1/7)
    previous_stock=np.bincount(state,minlength=7)
    for day in range(1,s.days+1):
        drng=np.random.default_rng(s.seed+day*1009)
        old=state.copy()
        arriving=cohort==day;state[arriving]=0
        state[(state==5)]=1
        inactive=state==4
        returning=inactive&(drng.random(n)<day_return)
        state[returning]=5
        active=np.isin(state,[0,1,2,5])
        leaving=active&~arriving&~returning&(drng.random(n)<day_exit)
        state[leaving]=4
        # Organic buying follows time in the audience and does not require ads.
        organic_age=np.clip(day-np.maximum(1,cohort)+1,0,response_horizon)
        # Organic response occurs regardless of advertising; it is reported
        # separately and cannot be attributed to the campaign.
        active=np.isin(state,[0,1,2,5])
        organic=active&(organic_threshold<baseline*cdf[group,organic_age])
        organic_responded[organic]=True;organic_response_day[organic]=day;state[organic]=3
        active=np.isin(state,[0,1,2,5])
        eligible=np.flatnonzero(active)
        if s.eligible_profiles is not None:
            eligible=eligible[np.isin(group[eligible],s.eligible_profiles)]
        # Breadth is the top fraction of the current active population by
        # benchmark response. Freeze that fraction before enforcing caps.
        if len(eligible):
            tie=np.mod(customers.customer_id.to_numpy()*0.61803398875,1)
            ranking=np.lexsort((tie[eligible],-lift[eligible]))
            eligible=eligible[ranking[:max(1,int(np.ceil(len(eligible)*s.breadth/100)))]]
            eligible=eligible[contacts[eligible]<s.contact_cap]
        quota=s.contact_budget*day//s.days-s.contact_budget*(day-1)//s.days
        # One recorded contact/person/day. Unavailable quota is not spent.
        fresh=eligible[contacts[eligible]==0];repeat=eligible[contacts[eligible]>0]
        repeat=drng.permutation(repeat);fresh=drng.permutation(fresh)
        nr=min(len(repeat),round(quota*s.repeat_share/100))
        nf=min(len(fresh),quota-nr)
        nr=min(len(repeat),quota-nf)
        selected=np.r_[repeat[:nr],fresh[:nf]]
        newly_contacted=selected[first_contact_day[selected]<0]
        first_contact_day[newly_contacted]=day
        contacts[selected]+=1;touched[selected]=True
        exposure=np.zeros(n,dtype=bool);exposure[selected]=True
        active=np.isin(state,[0,1,2,5])
        # Contact day is response day 1. Repeats and returns do not restart it.
        ad_age=np.where(touched,np.clip(day-first_contact_day+1,1,response_horizon),0)
        inc=active&touched&(ad_threshold<lift*cdf[group,ad_age]*frequency[group,contacts])
        ad_responded[inc]=True;ad_response_day[inc]=day;state[inc]=3
        # Illustrative lifecycle movement. These rates are deliberately
        # independent from the calibrated conversion probabilities.
        draw=drng.random(n)
        became_ready=(state==1)&(draw<(.012+.085*exposure))
        became_engaged=(state==0)&(draw<(.018+.12*exposure))
        state[became_ready]=2;state[became_engaged]=1
        history[day]=state;contact_history[day]=contacts
        changed=np.flatnonzero(old!=state)
        if record_events:
            events.append(pd.DataFrame(dict(customer_id=selected+1,day=day,contact_number=contacts[selected],segment_id=group[selected],is_repeat=contacts[selected]>1)))
            transitions.append(pd.DataFrame(dict(customer_id=changed+1,day=day,from_state=old[changed],to_state=state[changed],segment_id=group[changed])))
        flow=np.bincount(old.astype(int)*7+state,minlength=49).reshape(7,7)
        for fr,to in zip(*np.nonzero(flow)):
            flows.append(dict(day=day,source=STATES[fr],target=STATES[to],customers=int(flow[fr,to])))
        stock=np.bincount(state,minlength=7)
        assert int(stock.sum())==n
        daily.append(dict(day=day,new_arrivals=int(arriving.sum()),returning=int(returning.sum()),departures=int(leaving.sum()),contacts=len(selected),repeat_contacts=int(nr),new_contacts=int(nf),unused_contacts=int(quota-len(selected)),cumulative_contacts=int(contacts.sum()),unique_reached=int(touched.sum()),ad_responses=int(ad_responded.sum()),organic_responses=int(organic_responded.sum()),active=int(stock[[0,1,2,5]].sum()),new=int(stock[0]),engaged=int(stock[1]),ready=int(stock[2]),responded=int(stock[3]),inactive=int(stock[4])))
    customers['final_state']=[STATES[x] for x in state]
    customers['contacts']=contacts
    customers['ad_response']=ad_responded
    customers['organic_response']=organic_responded
    customers['first_contact_day']=first_contact_day
    customers['ad_response_day']=ad_response_day
    customers['organic_response_day']=organic_response_day
    customers['profile']=np.array(GROUPS)[group]
    profiles=customers.groupby('segment_id').agg(customers=('customer_id','size'),contacts=('contacts','sum'),unique_reached=('contacts',lambda x:int((x>0).sum())),ad_responses=('ad_response','sum'),organic_responses=('organic_response','sum')).reset_index()
    assert contacts.max()<=s.contact_cap
    assert contacts.sum()<=s.contact_budget
    assert not (ad_responded&organic_responded).any()
    return dict(customers=customers,daily=pd.DataFrame(daily),flows=pd.DataFrame(flows),profiles=profiles,history=history,contact_history=contact_history,scenario=asdict(s),contacts=pd.concat(events,ignore_index=True) if events else pd.DataFrame(),transitions=pd.concat(transitions,ignore_index=True) if transitions else pd.DataFrame())

def cohort_summary(result,measure='Active customers'):
    rows=[];p=result['customers'];cohort=p.arrival_day.to_numpy()
    for week in range(0,5):
        selected=(cohort==0) if week==0 else ((cohort>7*(week-1))&(cohort<=7*week))
        if not selected.any():continue
        for day in range(1,result['scenario']['days']+1):
            entered=selected&(cohort<=day)
            n=int(entered.sum())
            if not n:continue
            state=result['history'][day,entered];c=result['contact_history'][day,entered]
            value=int(np.isin(state,[0,1,2,5]).sum()) if measure=='Active customers' else int((c>0).sum()) if measure=='Reached customers' else int((state==3).sum())
            rows.append(dict(cohort='Starting audience' if week==0 else f'Week {week} arrivals',day=day,customers=value,share=100*value/n,cohort_size=n))
    return pd.DataFrame(rows)
