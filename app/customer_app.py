"""Campaign Runway: a guided live presentation with a basic Gemini sidebar."""
from pathlib import Path
import sys,json
import numpy as np
import pandas as pd
import streamlit as st

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.customer_lab import Scenario,load_calibration,simulate,GROUPS,COLORS,SIMULATION_VERSION
from app.story_charts import cumulative_chart,trace_sample,customer_animation,scorecard,POLICIES,POLICY_COLORS
from app.audience_visuals import audience_overview,shopping_averages,response_tiles,advertising_comparison
from app.repetition_visuals import render_repetition_rows
from src.exposure_reference import build_exposure_reference
from src.retail_metadata import GROUP_RULES
from app.scroll_story import install_scroll_story
from app.theme import SITE_CSS,landing_tradeoff
from app.sidebar_chat import render_sidebar_chat
from app.audience_selection import render_audience_selection
from app.analyst_navigation import install_analyst_navigation

st.set_page_config(page_title='Campaign Runway',page_icon='◌',layout='wide')
st.html(f'<style>{SITE_CSS}</style>')
st.html(f'<style>{(ROOT/"app/sidebar_chat.css").read_text()}</style>')

DATA=ROOT/'app/data/customer_lab'
if not (DATA/'provenance.json').exists():
    st.error('Prepare the customer dataset first.');st.code(r'.\.venv\Scripts\python.exe scripts/prepare_customer_lab.py');st.stop()

@st.cache_data(show_spinner=False)
def calibration(signature):return load_calibration(DATA)

@st.cache_data(show_spinner=False,max_entries=6)
def run_campaign(s,signature,model_version):return simulate(s,calibration(signature))

signature=tuple(p.stat().st_mtime_ns for p in sorted(DATA.glob('*')) if p.is_file())
cal=calibration(signature)
if st.session_state.get('simulation_version')!=SIMULATION_VERSION:
    st.session_state.pop('comparison_run',None)
    st.session_state['playing']=False
    st.session_state['simulation_version']=SIMULATION_VERSION
data_version=json.loads((DATA/'provenance.json').read_text()).get('version','original')
if st.session_state.get('retail_data_version')!=data_version:
    for key in ['selected_profile','pattern_profile','focus_groups','wide_groups','comparison_run','saved_settings','campaign_days','response_checkpoint']:
        st.session_state.pop(key,None)
    st.session_state['playing']=False;st.session_state['retail_data_version']=data_version
DEFAULTS={'response_checkpoint':3,'repetition_profile':-1,
          'campaign_days':30,'contact_budget':75000,'initial_population':100000,'arrival_rate':15,'turnover_rate':10,'return_rate':8,
          'focus_groups':[4],'wide_groups':[0,1,2,3,4],'focus_cap':4,'wide_cap':3,'focus_repeat':50,'wide_repeat':20,
          'play_speed':'Normal','frame_day':0,'playing':False}
# Keep main-page settings when their section is not currently rendered.
for key,default in DEFAULTS.items():
    fallback=st.session_state.get('saved_settings',{}).get(key,default)
    st.session_state[key]=st.session_state.get(key,fallback)

render_sidebar_chat(cal)

brand,about=st.columns([5,1])
with brand:st.html('<div class="eyebrow">CAMPAIGN RUNWAY / AN AUDIENCE STORY</div>')
with about:
    with st.popover('About this demo'):
        st.markdown('**Real advertising patterns. Synthetic customer scenarios.**')
        st.write('Criteo uplift records calibrate response potential. Impression histories provide a base for timing and contacts; a declared retail decision layer adds different deliberation and familiarity needs. Customer missions, CRM attributes and individual outcomes are synthetic.')
        st.write('Customer identities, lifecycle movement and individual outcomes are simulated. Results support a proposed pilot, not a proven advertising policy.')
        st.markdown('[Criteo dataset description](https://ailab.criteo.com/criteo-uplift-prediction-dataset/)')

install_scroll_story()

with st.container(key='chapter_question'):
    st.html('<div class="step-label" id="the-question">01 / THE CLIENT’S DECISION</div>')
    left,right=st.columns([1.3,1],gap='large',vertical_alignment='center')
    with left:
        st.html('''<div class="hero-copy"><div class="hero-kicker">CAMPAIGN RUNWAY</div>
        <h1 class="hero-title">Who deserves<br><span>the next ad?</span></h1>
        <p class="hero-lead">Should we keep advertising to our most responsive customers—or spend that capacity reaching someone new?</p>
        <a class="story-continue hero-cta" href="#meet-the-audience">Meet the audience <span>↗</span></a></div>''')
    with right:st.image(landing_tradeoff(),width='stretch')
    st.html('''<div class="brief-grid"><div class="brief-card"><div class="card-label">THE CLIENT</div><h3>Who is this site for?</h3><p>A campaign manager at a fictional online retailer, promoting a featured collection.</p></div><div class="brief-card"><div class="card-label">THE BUSINESS PAIN</div><h3>What problem do we solve?</h3><p>Every repeat advertisement uses a contact that could reach a new customer. The manager needs to decide how to divide a limited budget.</p></div></div>''')
    a,b=st.columns(2,gap='medium')
    with a:
        st.html('''<div class="journey-card"><div class="journey-number">01</div><div><h3>First, understand the audience</h3><p>Who responds, how quickly, and after how many recorded contacts?</p></div></div>''')
    with b:
        st.html('''<div class="journey-card phase-two"><div class="journey-number">02</div><div><h3>Then, test the campaign</h3><p>Build a focused campaign and a wide-reach campaign. Watch their results accumulate in the same changing customer base.</p></div></div>''')
    st.html('<div class="hero-footer"><span>One decision. Two approaches. The same available contact budget.</span><span class="scroll-hint">SCROLL TO EXPLORE ↓</span></div>')

with st.container(key='chapter_audience'):
    st.html('<div class="step-label">02 / UNDERSTAND THE CUSTOMER BASE</div>')
    st.title('Meet the audience')
    st.write('Five shopping missions. Different baskets, buying rhythms and reasons to come back.')
    mix,habits,advertising,timing=st.tabs(['Customer groups','Shopping differences','Conversion rates','Response timing'],key='audience_tab',on_change='rerun')
    with mix:
        st.subheader('The whole customer base, largest to smallest')
        render_audience_selection(cal)
        st.caption('Constructed CRM groups, selected by shopping interests, preferences and purchase history.')
    with habits:
        left,right=st.columns(2)
        with left:
            st.subheader('Average purchases per year')
            st.altair_chart(shopping_averages(cal['templates'],'orders_last_year',st.session_state['repetition_profile']),width='stretch')
        with right:
            st.subheader('Average basket size')
            st.altair_chart(shopping_averages(cal['templates'],'typical_basket',st.session_state['repetition_profile']),width='stretch')
        st.caption('Means across all customer profiles in each group. Purchases count orders in the past year; basket size averages each customer’s typical order value.')
        st.html('<div class="insight-card"><strong>Frequency and basket size answer different questions.</strong> Household regulars and convenience shoppers buy most often. Specialist enthusiasts have the largest average baskets.</div>')
    with advertising:
        st.subheader('Who shows the biggest difference with advertising?')
        st.markdown('**Grey dot: without advertising** · **Group-coloured dot: with advertising**')
        st.altair_chart(advertising_comparison(cal['groups'],'Conversion rate (%)',st.session_state['repetition_profile']),width='stretch')
        g=cal['groups'].set_index('segment_id');conv=g.loc[4];regular=g.loc[0]
        st.html(f'<div class="insight-card"><strong>Buying often and responding to ads are different traits.</strong> Convenience shoppers move from {conv.baseline_rate*100:.2f}% to {(conv.baseline_rate+conv.incremental_rate)*100:.2f}% conversion with advertising. Household regulars move from {regular.baseline_rate*100:.2f}% to {(regular.baseline_rate+regular.incremental_rate)*100:.2f}%. The gap between the dots shows the difference.</div>')
        st.caption('Matched benchmark conversion rates for the constructed audiences. The chart compares rates, not campaign outcomes.')
    with timing:
        a,b=st.columns([1,2])
        with a:
            st.subheader('Follow the first 30 days')
            day=st.select_slider('Days since first contact',options=[1,2,3,5,7,10,14,21,30],key='response_checkpoint',format_func=lambda x:f'Day {x}')
        with b:
            checkpoint=cal['shapes'].query('day==@day').set_index('segment_id').response_share
            fast=int(checkpoint.idxmax());slow=int(checkpoint.idxmin());gap=(checkpoint.max()-checkpoint.min())*100
            if gap>=1:
                st.html(f'<div class="insight-card"><strong>{GROUPS[fast]} respond sooner than {GROUPS[slow].lower()}.</strong><br>By day {day}, {checkpoint.loc[fast]*100:.0f}% of their eventual responses have arrived, compared with {checkpoint.loc[slow]*100:.0f}%. Move through the days to watch the difference.</div>')
            else:st.html('<div class="insight-card"><strong>At day 30, every panel is complete.</strong><br>The timing difference is how quickly each audience got here. Move back to an earlier day to see it.</div>')
        st.image(response_tiles(cal['shapes'],day,st.session_state['repetition_profile']),width='stretch')
        st.caption('100 dots = 100 eventual 30-day responders in each group. Filled = responded by this day; pale = later. These are shares of responders, not conversion rates.')
    footer_info,footer_next=st.columns([3,2],vertical_alignment='top')
    with footer_info:
        with st.expander('Data and response definitions'):
            st.write('The source histories supply the base response shapes. Retail metadata adds explicit assumptions: easy reorders and offers move faster; occasion purchases and specialist decisions take longer. A familiarity requirement shifts some response paths to later contacts. The raw source histories are retained unchanged; these views show the resulting synthetic scenario used by the campaign simulation.')
            st.write('The 30-day retail clock maps the source’s 14-day follow-up onto a synthetic month-long scenario. Timing is normalized within that scenario. Time and contact count are separate marginal views, not a joint causal estimate of when a particular person will buy. Benchmark response magnitude comes from the matched uplift records.')
    with footer_next:
        st.html('<a class="story-continue" href="#repeated-exposure">Now explore what repetition adds <span>↓</span></a>')

with st.container(key='chapter_patterns'):
    st.html('<div class="step-label" id="repeated-exposure">03 / THE VALUE OF CONTINUED EXPOSURE</div>')
    st.title('Where does repetition keep finding customers?')
    st.html('<div class="reference-strip"><div><strong>30 days</strong><span>fixed response window</span></div><div><strong>100,000 customers</strong><span>starting audience in EACH group</span></div><div><strong>1–12 exposures</strong><span>ad counts, not calendar days</span></div></div>')
    selected=st.session_state['repetition_profile']
    if 'exposure_detail' in cal and 'exposure_stages' in cal:
        detail,stages=cal['exposure_detail'],cal['exposure_stages']
    else:detail,stages=build_exposure_reference(cal)
    gains,conclusions=st.tabs(['What each stage adds','What we learned'],key='exposure_tab',on_change='rerun')
    with gains:
        st.markdown('**Additional advertising-associated responders at each exposure stage**')
        render_repetition_rows(stages,selected)
        st.caption('One full dot ≈ 2 additional responders. Ads delivered include contacts to nonresponders.')
    with conclusions:
        st.subheader('The audience calls for different follow-up strategies')
        s=stages.set_index(['segment_id','stage_id'])
        conv_early=float(s.loc[(4,1),'coverage'])*100;bargain_early=float(s.loc[(1,1),'coverage'])*100
        specialist_first=100*float(s.loc[(3,0),'responses_per_1000_contacts'])
        specialist_repeat=100*float(s.loc[(3,2),'responses_per_1000_contacts'])
        findings=[
            ('Convenience & bargain shoppers: front-loaded response',f'{conv_early:.0f}% of convenience response potential and {bargain_early:.0f}% of bargain response potential appears in the first two exposures. Later contacts find progressively fewer additional responders.'),
            ('Specialists: response builds after repeats',f'For the same 100,000 ads, the 3rd–4th exposures return {specialist_repeat:.1f} modeled responders, versus {specialist_first:.1f} on first exposure. Repetition matters more for this group.'),
            ('Occasion shoppers: one reminder stands out',f'The second exposure adds {s.loc[(2,1),"additional_responses"]:.1f} responders, versus {s.loc[(2,0),"additional_responses"]:.1f} on first exposure. The return per ad drops at later stages.'),
            ('Household regulars: frequent buying, smaller ad uplift','They buy frequently, but their advertising-associated increase is comparatively small. Audience size and purchase frequency alone do not justify repeated advertising.'),
        ]
        cols=st.columns(2)
        for i,(title,body) in enumerate(findings):
            active=st.session_state.get('demo_step') is not None and st.session_state.get('demo_conclusion')==i
            with cols[i%2]:st.html(f'<div class="conclusion-card{" conclusion-active" if active else ""}"><h3>{title}</h3><p>{body}</p></div>')
        st.html('<div class="statement">A single repeat-ad schedule does not suit every group.</div>')
        st.write('These findings identify where early reach or continued exposure may be useful. Phase 2 tests how to divide the budget between them as customers arrive and leave.')
    footer_info,footer_next=st.columns([3,2],vertical_alignment='top')
    with footer_info:
        with st.expander('The fixed reference behind this comparison'):
            st.write('This is a precomputed exposure reference, not a configurable campaign. Each group starts with 100,000 customers. Everyone who has not yet produced an advertising-associated response receives the next exposure, including eventual nonresponders. Responders leave the advertising pool. Only advertising-associated responses are counted; organic purchases are not simulated here.')
            st.write('Response potential equals the group’s benchmark incremental conversion rate. Exposure coverage allocates that potential across contacts. Additional response is the difference between successive exposure totals; response per ad divides by all contacts delivered. The full 30-day response potential is held fixed to isolate exposure count. Exposures are not days.')
            st.write('These are synthetic reference expectations calibrated from source patterns, not measured causal effects of another ad. Phase 2 adds budgets, delivery timing, customer arrivals and turnover to test competing campaign strategies.')
    with footer_next:
        st.html('<a class="story-continue" href="#campaign-simulation">Test the tradeoff with a campaign <span>↓</span></a>')

with st.container(key='chapter_simulation'):
    st.html('<div class="step-label" id="campaign-simulation">04 / PHASE 2 — TRY THE DECISION</div>')
    st.title('Build two campaigns. Watch what happens.')
    has_run='comparison_run' in st.session_state
    with st.expander('Edit campaign settings' if has_run else 'Campaign settings',expanded=not has_run or st.session_state.pop('campaign_settings_open',False)):
        with st.form('campaign_settings'):
            st.markdown('**The same starting point**')
            st.caption('Starting customers come from the groups selected in either campaign. Both campaigns share those people; mixed audiences keep the groups’ relative proportions.')
            a,b,c=st.columns(3)
            with a:population=st.selectbox('Starting customers',[25000,50000,100000,200000],key='initial_population',format_func=lambda x:f'{x:,}')
            with b:budget=st.number_input('Available ad contacts',min_value=0,max_value=1000000,step=10000,key='contact_budget')
            with c:days=st.select_slider('Campaign length',options=[7,14,21,30],key='campaign_days',format_func=lambda x:f'{x} days')
            left,right=st.columns(2)
            with left:
                st.markdown('### Focused campaign')
                focus=st.multiselect('Eligible customer groups',range(5),format_func=lambda x:GROUPS[x],key='focus_groups')
                fcap=st.slider('Contact cap per customer',1,12,key='focus_cap')
                frepeat=st.slider('Prefer repeat contacts (%)',0,100,step=5,key='focus_repeat')
            with right:
                st.markdown('### Wide-reach campaign')
                wide=st.multiselect('Eligible customer groups',range(5),format_func=lambda x:GROUPS[x],key='wide_groups')
                wcap=st.slider('Contact cap per customer',1,12,key='wide_cap')
                wrepeat=st.slider('Prefer repeat contacts (%)',0,100,step=5,key='wide_repeat')
            with st.expander('Change the customer environment'):
                a,b,c=st.columns(3)
                with a:arrivals=st.slider('New audience arrivals per week (%)',0,40,step=5,key='arrival_rate')
                with b:turnover=st.slider('Weekly customer turnover (%)',0,40,step=5,key='turnover_rate')
                with c:returns=st.slider('Inactive customers returning (%)',0,30,step=2,key='return_rate')
            submitted=st.form_submit_button('Run comparison',type='primary',key='run_comparison')
    if submitted or st.session_state.pop('demo_run_requested',False):
        st.session_state['saved_settings']={key:st.session_state[key] for key in ['initial_population','contact_budget','campaign_days','focus_groups','wide_groups','focus_cap','wide_cap','focus_repeat','wide_repeat','arrival_rate','turnover_rate','return_rate']}
        if not focus or not wide:st.error('Choose at least one customer group for each campaign.')
        else:
            shared_groups=tuple(sorted(set(focus)|set(wide)))
            common=dict(population=population,days=days,contact_budget=budget,breadth=100.,weekly_arrivals=float(arrivals),weekly_turnover=float(turnover),weekly_return=float(returns),population_profiles=shared_groups)
            scenarios={POLICIES[0]:Scenario(**common,contact_cap=fcap,repeat_share=float(frepeat),eligible_profiles=tuple(sorted(focus))),POLICIES[1]:Scenario(**common,contact_cap=wcap,repeat_share=float(wrepeat),eligible_profiles=tuple(sorted(wide)))}
            with st.spinner('Preparing the same customer population for both campaigns…'):
                results={label:run_campaign(s,signature,SIMULATION_VERSION) for label,s in scenarios.items()}
            st.session_state['comparison_run']={'results':results,'scenarios':scenarios,'traces':trace_sample(results),'signature':signature,'model_version':SIMULATION_VERSION}
            st.session_state['frame_day']=0;st.session_state['playing']=True
            st.rerun()
    run=st.session_state.get('comparison_run')
    if run:
        st.html('<hr class="small-rule">')
        population_rows=next(iter(run['results'].values()))['customers']
        initial=population_rows[population_rows.arrival_day.eq(0)]
        mix=initial.segment_id.value_counts().sort_index()
        st.markdown(f'**Shared starting audience: {len(initial):,} customers**')
        st.write(' · '.join(f'{GROUPS[int(gid)]}: {count:,} ({100*count/len(initial):.1f}%)' for gid,count in mix.items()))
        speed=st.select_slider('Playback speed',options=['Slow','Normal','Fast'],key='play_speed')
        interval={'Slow':1.4,'Normal':.8,'Fast':.4}[speed]
        @st.fragment(run_every=interval if st.session_state.playing else None)
        def playback():
            results=st.session_state.comparison_run['results'];duration=next(iter(results.values()))['scenario']['days']
            if st.session_state.playing:st.session_state['frame_day']=min(duration,st.session_state.frame_day+1)
            day=st.session_state.frame_day
            if day==duration and st.session_state.playing:
                st.session_state['playing']=False;st.rerun()
            a,b,c,d,e=st.columns([1.1,1.1,1.1,1.2,1])
            if a.button('Pause' if st.session_state.playing else 'Resume',key='play_pause',disabled=day==duration):
                st.session_state['playing']=not st.session_state.playing;st.rerun()
            if b.button('Next day',key='play_next',disabled=day==duration):
                st.session_state['playing']=False;st.session_state['frame_day']=min(duration,day+1);st.rerun()
            if c.button('Replay',key='play_replay'):
                st.session_state['playing']=True;st.session_state['frame_day']=0;st.rerun()
            if d.button('Show final day',key='play_final'):
                st.session_state['playing']=False;st.session_state['frame_day']=duration;st.rerun()
            e.markdown(f'**Day {day} / {duration}**')
            st.progress(day/duration)
            st.caption('Illustrative traces emphasize responders; all totals and curves use the full synthetic population.')
            a,b,c=st.columns([1,1,1.2])
            for col,(label,r),color in zip([a,b],results.items(),POLICY_COLORS):
                with col:
                    st.markdown(f'**{label}**')
                    st.iframe(customer_animation(r,day,run['traces'],color),height='content',alt=f'{label} synthetic customer movement on day {day}')
                    values=r['daily'].iloc[day-1] if day else pd.Series({'ad_responses':0,'unique_reached':0,'cumulative_contacts':0})
                    st.metric('Ad-driven responses',f'{int(values.ad_responses):,}')
                    st.write(f'**{int(values.unique_reached):,}** reached · **{int(values.cumulative_contacts):,}** contacts')
            with c:
                st.markdown('**Response, as it accumulates**')
                st.altair_chart(cumulative_chart(results,day,duration),width='stretch',key='live_response_chart')
            if day==duration:
                st.dataframe(scorecard(results),hide_index=True,width='stretch')
        with st.container(key='simulation_playback'):playback()
    else:
        st.write('Set the two approaches above, then run them against the same customer base.')

with st.container(key='chapter_answer'):
    st.html('<div class="step-label" id="campaign-answer">05 / RETURN TO THE CLIENT’S QUESTION</div>')
    st.title('Who should receive the next ad?')
    run=st.session_state.get('comparison_run')
    if not run:
        st.write('Run the two campaigns to build an answer from their results.')
        st.html('<a class="story-continue" href="#campaign-simulation">Build the comparison ↑</a>')
    else:
        results=run['results'];scores=scorecard(results)
        duration=next(iter(results.values()))['scenario']['days']
        st.altair_chart(cumulative_chart(results,duration,duration),width='stretch')
        st.dataframe(scores,hide_index=True,width='stretch')
        x,y=scores.iloc[0],scores.iloc[1]
        diff=int(x['Ad-driven responses']-y['Ad-driven responses'])
        if diff:
            winner=POLICIES[0] if diff>0 else POLICIES[1]
            st.html(f'<div class="statement">In this scenario, the {winner.lower()} generates {abs(diff):,} more modeled ad-driven responses.</div>')
        else:st.html('<div class="statement">The two approaches produce the same modeled ad-driven response. Reach and contact use distinguish them.</div>')
        st.write('Choose a policy to pilot by weighing response, reach and unused capacity. Change turnover or arrivals to test whether that choice holds.')
        st.html('<a class="story-continue" href="#campaign-simulation">Test another assumption ↑</a>')
        st.download_button('Download the comparison',scores.to_csv(index=False),'campaign-comparison.csv','text/csv')

    with st.expander('Sources & model assumptions'):
        st.write('Real Criteo benchmark patterns; synthetic retail missions, CRM attributes, identities and outcomes. A versioned allocation and latent-cell bridge connect the sources. No original feature meanings or shared customer identities are claimed.')
        st.write('A new arrival is newly reachable by the campaign, not necessarily a first-time retail customer. Synthetic prior orders span all store categories; the campaign response concerns its promoted collection. Turnover is a scenario assumption weighted by synthetic purchase history and promotion preference.')
        st.write('Both campaigns share one population formed from all groups selected in either campaign, with their relative population shares preserved. Arrivals use the same mix. Campaign eligibility remains separate. One contact per customer per day; caps apply over the campaign; unused daily capacity expires. Responded customers leave the advertising pool. Advertising response time starts at first contact; organic response time starts when a customer enters the audience. Neither clock restarts on repeat ads or returning to the active audience.')
        st.write('Organic purchase rates use 20% of the benchmark-derived baseline in both campaigns. This scenario adjustment reduces background purchases; advertising response potential is unchanged.')
        st.write('Customer traces intentionally include responders for visibility and are not a proportional population sample. The numerical counters use all customers. Simulated differences are not proof of a real causal policy advantage.')
        st.markdown('[Criteo uplift](https://ailab.criteo.com/criteo-uplift-prediction-dataset/) · [Criteo attribution](https://ailab.criteo.com/criteo-attribution-modeling-bidding-dataset/)')
        run=st.session_state.get('comparison_run')
        if run:
            st.download_button('Download scenario settings',json.dumps({label:r['scenario'] for label,r in run['results'].items()},indent=2),'campaign-settings.json','application/json')

install_analyst_navigation()
