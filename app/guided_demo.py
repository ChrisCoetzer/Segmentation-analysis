"""Evidence-led tour: customer missions, comparisons, conclusions and a worked simulation."""
import re
from uuid import uuid4
import streamlit as st
from src.customer_lab import GROUPS

DEMO_VERSION='evidence-walkthrough-v3-specialist-example'
EXAMPLE_SETTINGS=dict(initial_population=100000,contact_budget=250000,campaign_days=30,
    focus_groups=[3],wide_groups=[0,1,2,3,4],focus_cap=8,wide_cap=1,
    focus_repeat=90,wide_repeat=0,arrival_rate=15,turnover_rate=10,return_rate=8)
def step(key,title,section,tab=None,group=-1,day=None,conclusion=None,kind=None,frame=None):
    return dict(key=key,title=title,section=section,tab=tab,group=group,day=day,conclusion=conclusion,kind=kind,frame=frame)
STEPS=[
    step('question','The advertising allocation decision','question'),
    step('groups','Customer groups and selection criteria','audience','Customer groups'),
    step('household','Household regulars: a replenishment mission','audience','Customer groups',0),
    step('household_habits','Purchase frequency and basket size','audience','Shopping differences',0),
    step('household_conversion','Advertising-associated conversion','audience','Conversion rates',0),
    step('bargain','Bargain hunters: promotion preference','audience','Customer groups',1),
    step('bargain_conversion','A different advertising response','audience','Conversion rates',1),
    step('bargain_timing','Bargain hunter response timing','audience','Response timing',1,3),
    step('occasion','Occasion shoppers: a deadline-driven purchase','audience','Customer groups',2),
    step('occasion_timing','Occasion shopper response timing','audience','Response timing',2,7),
    step('specialist','Specialists: category interest and careful delivery','audience','Customer groups',3),
    step('specialist_habits','Specialist purchase frequency and basket size','audience','Shopping differences',3),
    step('specialist_timing','Specialist response timing','audience','Response timing',3,7),
    step('convenience','Convenience shoppers: easy repeat purchasing','audience','Customer groups',4),
    step('convenience_conversion','Convenience shopper conversion','audience','Conversion rates',4),
    step('convenience_timing','Convenience shopper response timing','audience','Response timing',4,3),
    step('timing_denominator','The response-timing denominator','audience','Response timing',-1,30),
    step('exposure_overview','How to read What each stage adds','exposure','What each stage adds'),
    step('exposure_early','Convenience shopper exposure response','exposure','What each stage adds',4),
    step('exposure_late','Specialist exposure response','exposure','What each stage adds',3),
    step('finding_early','Conclusion 1: front-loaded response','exposure','What we learned',conclusion=0),
    step('proof_early','Evidence: convenience shopper exposure response','exposure','What each stage adds',4),
    step('proof_bargain','Evidence: bargain hunter exposure response','exposure','What each stage adds',1),
    step('finding_specialist','Conclusion 2: specialists build after repeats','exposure','What we learned',conclusion=1),
    step('proof_specialist','Account for ads delivered','exposure','What each stage adds',3),
    step('finding_occasion','Conclusion 3: one reminder stands out','exposure','What we learned',conclusion=2),
    step('proof_occasion','Evidence: first and second occasion contacts','exposure','What each stage adds',2),
    step('finding_household','Conclusion 4: frequent buying, smaller uplift','exposure','What we learned',conclusion=3),
    step('proof_household','Revisit the conversion benchmark','audience','Conversion rates',0),
    step('mandate','Implications for advertising allocation','exposure','What we learned'),
    step('example_setup','Example: specialist follow-up or wider reach?','simulation',kind='preset'),
    step('example_run','Run the example campaign comparison','simulation',kind='run'),
    step('example_week','Campaign comparison at day 7','simulation',kind='result',frame=7),
    step('example_final','Campaign comparison at day 30','simulation',kind='result',frame=30),
    step('answer','Return to the client’s decision','answer',kind='result',frame=30),
]
def is_demo_request(prompt):
    return bool(re.fullmatch(r'(?:hey[,! .]*)?(?:please )?(?:give me a demo|show me a demo|start (?:the |a )?(?:guided )?(?:demo|tour)|walk me through (?:the |this )?site|demo)(?: of (?:the |this )?(?:site|website))?(?: please)?[.!?]*',prompt.lower().strip()))
def example_matches(run):
    if not run or len(run.get('results',{}))!=2:return False
    for result,prefix in zip(run['results'].values(),['focus','wide']):
        s=result['scenario']
        expected=dict(population=EXAMPLE_SETTINGS['initial_population'],days=EXAMPLE_SETTINGS['campaign_days'],contact_budget=EXAMPLE_SETTINGS['contact_budget'],weekly_arrivals=15.,weekly_turnover=10.,weekly_return=8.,
            contact_cap=EXAMPLE_SETTINGS[prefix+'_cap'],repeat_share=float(EXAMPLE_SETTINGS[prefix+'_repeat']))
        if any(s.get(k)!=v for k,v in expected.items()):return False
        if tuple(s.get('eligible_profiles') or ())!=tuple(EXAMPLE_SETTINGS[prefix+'_groups']):return False
    return True
def go_to_step(state,index):
    index=max(0,min(len(STEPS)-1,index));s=STEPS[index]
    matching=example_matches(state.get('comparison_run'))
    if s['kind']=='result' and not matching and index>=state.get('demo_step',0):return False
    state['demo_version']=DEMO_VERSION;state['demo_step']=index
    state['repetition_profile']=s['group'];state['demo_conclusion']=s['conclusion']
    if s['tab']:state['audience_tab' if s['section']=='audience' else 'exposure_tab']=s['tab']
    if s['day'] is not None:state['response_checkpoint']=s['day']
    if s['kind']=='preset':
        state.update({k:list(v) if isinstance(v,list) else v for k,v in EXAMPLE_SETTINGS.items()})
        state['saved_settings']={k:state[k] for k in EXAMPLE_SETTINGS}
    if s['section']=='simulation':state['campaign_settings_open']=s['kind'] in ['preset','run']
    if s['frame'] is not None and matching:state['playing']=False;state['frame_day']=s['frame']
    state['analyst_navigation']={'section':s['section'],'highlight':False,
        'scroll_to':'playback' if s['frame'] is not None and s['section']=='simulation' else None,'token':uuid4().hex}
    return True
def start_demo():
    go_to_step(st.session_state,0)
    st.session_state.pop('analyst_error',None);st.session_state.pop('analyst_retry_prompt',None)
def move_demo(delta):go_to_step(st.session_state,st.session_state['demo_step']+delta)
def end_demo():
    for k in ['demo_step','demo_conclusion','demo_run_requested']:st.session_state.pop(k,None)
    st.session_state['analyst_navigation']={'section':'question','clear':True,'token':uuid4().hex}
def request_example():
    st.session_state.update({k:list(v) if isinstance(v,list) else v for k,v in EXAMPLE_SETTINGS.items()})
    st.session_state['demo_run_requested']=True

def narration(cal,state,index):
    s=STEPS[index];key=s['key'];gid=s['group']
    if s['kind']=='result' and not example_matches(state.get('comparison_run')):
        return 'Run the prepared example again before continuing.'
    groups=cal['groups'].set_index('segment_id')
    means=cal['templates'].groupby('segment_id')[['orders_last_year','typical_basket']].mean()
    stages=cal['exposure_stages'].set_index(['segment_id','stage_id'])
    def coverage(g):return float(stages.loc[(g,1),'coverage'])*100
    def added(g,k):return float(stages.loc[(g,k),'additional_responses'])
    def yield100k(g,k):return float(stages.loc[(g,k),'responses_per_1000_contacts'])*100
    fixed={
        'question':'Our client manages an online retailer’s advertising. The decision is how to divide a limited budget between repeat ads and reaching more customers.',
        'groups':'The bars show each group’s share of the audience; the criteria on the right explain membership. Groups are based on shopping interests, delivery preferences and purchase history.',
        'timing_denominator':'All panels reach 100% at day 30 because they track eventual responders. They show when responses arrive, not how many customers convert.',
        'exposure_overview':'Rows are customer groups; columns are exposure stages. Numbers and dots show additional responders, with about two per full dot. Ads delivered appear below each stage. Each group starts with 100,000 customers over 30 days.',
        'finding_specialist':'Specialists respond better after repeated contact. The next view checks whether that improvement holds after accounting for ads delivered.',
        'finding_occasion':'Occasion shoppers show a stronger response to the second contact. This supports one reminder rather than a long repeat schedule.',
        'finding_household':'Household regulars buy often, but advertising adds relatively little. Their conversion benchmark explains this finding.',
        'mandate':'The groups support different approaches: early reach for bargain and convenience shoppers, more follow-up for specialists, and one reminder for occasion shoppers. The simulation compares how these choices work in a campaign.',
        'example_setup':'Both campaigns start with **100,000 customers, 250,000 available contacts and 30 days**. The focused campaign targets specialists with up to 8 ads and 90% repeat preference. The wide campaign gives customers across all groups one ad.',
        'example_run':'Press **Run example**. The dots show a customer sample moving between reach and response states; green means responded and grey means inactive. The line chart tracks cumulative ad-driven responses by day: teal is focused, orange is wide. Counters use the full audience; All responses also includes organic purchases.',
    }
    if key in fixed:return fixed[key]
    definitions={
        'household':'Household interests, scheduled delivery and at least four orders a year identify regular replenishment customers.',
        'bargain':'A promotion preference of at least 75% identifies offer-led shoppers across categories.',
        'occasion':'Gift or seasonal interests, with delivery tied to an occasion, identify deadline-driven purchases.',
        'specialist':'Hobby, technology or outdoor interests and careful delivery identify considered equipment purchases.',
        'convenience':'Everyday essentials, fast delivery and at least two orders a year identify customers who prioritize convenience.',
    }
    if key in definitions:return f'**{GROUPS[gid]} make up {groups.loc[gid,"share"]*100:.0f}% of the audience.** '+definitions[key]
    if key in ['household_habits','specialist_habits']:
        intro='The left bars show average purchases per year; the right bars show average basket value. ' if key=='household_habits' else ''
        point='Frequent purchasing alone does not tell us whether more advertising helps.' if gid==0 else 'Specialists have the largest baskets. Their response timing is the next consideration.'
        return intro+f'**{GROUPS[gid]} average {means.loc[gid,"orders_last_year"]:.1f} purchases a year and a basket of USD {means.loc[gid,"typical_basket"]:.0f}.** '+point
    if key in ['household_conversion','bargain_conversion','convenience_conversion','proof_household']:
        r=groups.loc[gid]
        intro='Grey dots show conversion without ads; colored dots show conversion with ads. The gap is the advertising-associated increase. ' if key=='household_conversion' else ''
        point='The small gap means limited additional response from advertising.' if gid==0 else 'The gap shows how much advertising adds beyond existing purchasing.'
        return intro+f'For **{GROUPS[gid]}**, conversion rises from **{r.baseline_rate*100:.2f}% to {(r.baseline_rate+r.incremental_rate)*100:.2f}%**. '+point
    if key in ['bargain_timing','occasion_timing','specialist_timing','convenience_timing']:
        day=s['day'];v=cal['shapes'].query('day==@day').set_index('segment_id').response_share
        intro='Each panel represents 100 eventual 30-day responders. Filled dots show responses received by the selected day; pale dots are still to come. ' if key=='bargain_timing' else ''
        text=f'By **day {day}**, **{v.loc[gid]*100:.0f}%** of {GROUPS[gid].lower()} responses have arrived. '
        if gid==3:text+=f'Convenience shoppers are already at {v.loc[4]*100:.0f}%, showing the difference in timing.'
        elif gid==2:text+='A substantial share responds later in the window.'
        return intro+text
    if key in ['exposure_early','proof_early','proof_bargain']:
        return (f'The first two exposures capture **{coverage(gid):.0f}%** of {GROUPS[gid].lower()} response potential. '
                f'Exposures 5–8 add only **{added(gid,3):.1f}** more responders despite requiring four contact rounds.')
    if key in ['exposure_late','proof_specialist']:
        return (f'Specialists produce **{yield100k(3,0):.1f} responders per 100,000 ads** at first exposure, compared with **{yield100k(3,2):.1f}** at exposures 3–4. '
                'Repeat contact is more productive for this group, even after accounting for the extra ads.')
    if key=='finding_early':return (f'The first conclusion favors early reach: the first two ads capture **{coverage(4):.0f}%** of convenience response potential and **{coverage(1):.0f}%** of bargain response potential. The next views show their evidence.')
    if key=='proof_occasion':return (f'The second contact adds **{added(2,1):.1f}** responders, compared with **{added(2,0):.1f}** from the first. Later contacts produce diminishing returns.')
    results=state['comparison_run']['results'];day=s['frame'] or 30
    totals=[(label,r['daily'].iloc[day-1]) for label,r in results.items()]
    text=f'By **day {day}**, the focused campaign has **{int(totals[0][1].ad_responses):,} ad-driven responses**, compared with **{int(totals[1][1].ad_responses):,}** for wide reach. '
    if key=='example_week':return text+'This is an early checkpoint. The next step compares the full month.'
    if key=='example_final':return text+f'They reach **{int(totals[0][1].unique_reached):,}** and **{int(totals[1][1].unique_reached):,}** customers respectively. The wider campaign reaches more of the shared audience.'
    diff=int(totals[0][1].ad_responses)-int(totals[1][1].ad_responses)
    finding=f'**{totals[0 if diff>0 else 1][0]} adds {abs(diff):,} more modeled responses.** ' if diff else 'The modeled response totals are equal. '
    return finding+'Use the response and reach comparison to choose a pilot, then test other settings.'

def demo_context(cal,state):
    index=state.get('demo_step')
    if index is None or not 0<=index<len(STEPS):return None
    s=STEPS[index]
    return dict(step_number=index+1,step_count=len(STEPS),step_id=s['key'],title=s['title'],
        section=s['section'],tab=s['tab'],planned_group=GROUPS[s['group']] if s['group']>=0 else 'All groups',
        selected_group=GROUPS[state.get('repetition_profile',-1)] if state.get('repetition_profile',-1)>=0 else 'All groups',
        timing_checkpoint=s['day'],playback_checkpoint=s['frame'],conclusion_card_index=s['conclusion'],
        current_explanation=narration(cal,state,index),previous_step=STEPS[index-1]['title'] if index else None,
        next_step=STEPS[index+1]['title'] if index+1<len(STEPS) else None,
        example_settings=EXAMPLE_SETTINGS,matching_example_results_available=example_matches(state.get('comparison_run')))

def render_demo_controls(cal):
    index=st.session_state.get('demo_step')
    if index is None:return
    if st.session_state.get('demo_version')!=DEMO_VERSION:start_demo();index=0
    s=STEPS[index]
    with st.container(key='analyst_tour',border=True):
        st.caption(f'GUIDED DEMO · {index+1} / {len(STEPS)}')
        st.markdown(f'**{s["title"]}**');st.markdown(narration(cal,st.session_state,index))
        st.progress((index+1)/len(STEPS))
        if s['kind']=='run':st.button('Run example',key='demo_run_example',type='primary',on_click=request_example,width='stretch')
        back,next_,end=st.columns([1,1,1])
        back.button('Back',key='demo_back',disabled=index==0,on_click=move_demo,args=(-1,),width='stretch')
        if index==len(STEPS)-1:next_.button('Finish',key='demo_finish',on_click=end_demo,type='primary',width='stretch')
        else:next_.button('Next',key='demo_next',disabled=s['kind']=='run' and not example_matches(st.session_state.get('comparison_run')),
            on_click=move_demo,args=(1,),type='primary',width='stretch')
        end.button('End',key='demo_end',on_click=end_demo,width='stretch')
