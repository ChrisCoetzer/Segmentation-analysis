"""Streamlit segmentation demo. All model fitting happens offline."""
import json
from pathlib import Path
import sys

import pandas as pd
from scipy.stats import norm
import streamlit as st

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.charts import depth_chart

st.set_page_config(page_title='The Incrementality Lab',page_icon='📊',layout='wide')
DATA=Path(__file__).resolve().parent/'data'

@st.cache_data
def results(signature):
    return (pd.read_parquet(DATA/'groups.parquet'),
            json.loads((DATA/'run.json').read_text()))


if not all((DATA/name).exists() for name in ['groups.parquet','run.json']):
    st.title('The Incrementality Lab')
    st.info('Prepare the model results before opening the demo.')
    st.code('.\\.venv\\Scripts\\python.exe scripts/train_segmentation.py',language='powershell')
    st.stop()

groups,meta=results(tuple((DATA/name).stat().st_mtime_ns for name in
                                      ['groups.parquet','run.json']))
groups=groups[groups.segments<=32].copy()

def select_chart_segment():
    event=st.session_state.get('depth_chart',{})
    points=event.get('selection',{}).get('segment_pick',[])
    if points:
        count=int(points[0]['segments'])
        if count in groups.segments.unique():
            st.session_state['segments']=count

st.caption('THE INCREMENTALITY LAB / CUSTOMER SEGMENTATION')
st.title('How much customer detail is enough?')
st.markdown('**What did finer segmentation achieve in this dataset?**')
st.write('At each level, select the cluster with the highest advertising response estimated on separate data. '
         'Compare its average response using all evaluation users in that cluster.')
st.caption('f0–f11 only: four continuous features and eight categorical features. Advertising response is measured afterward.')
st.caption('Feature-only balanced clusters · 1 → 2 → 4 → 8 → 16 → 32')
with st.container(border=True):
    st.subheader('What does a more defined audience add?')
    outcome_label=st.radio('Outcome',['Conversions','Visits'],horizontal=True,index=0,key='outcome')
    available=sorted(groups.segments.unique().tolist())
    if st.session_state.get('segments',4) not in available:
        del st.session_state['segments']
    selected=st.session_state.get('segments',4)
    outcome={'Conversions':'conversion','Visits':'visit'}[outcome_label]
    unit='cluster_members'
    z=float(norm.ppf(.975))
    from src.segmentation import cluster_average_comparison
    current=cluster_average_comparison(groups,outcome)
    factor=10000
    broad=float(current.iloc[0]['value']*factor)
    current['relative_gain_percent']=(current['value']/current.iloc[0]['value']-1)*100
    chosen=current[current.segments==selected].iloc[0]
    mode=st.radio('Chart measure',['Incremental outcomes','Gain over broad targeting'],horizontal=True,key='measure')
    value,se=('value','se') if mode=='Incremental outcomes' else ('gain','gain_se')
    current['estimate']=current[value]*factor
    current['lower']=(current[value]-z*current[se])*factor
    current['upper']=(current[value]+z*current[se])*factor
    current['denominator']=unit
    title=f'{"Additional" if value=="gain" else "Incremental"} {outcome_label.lower()} per 10,000 cluster members'
    st.caption('Click a point to inspect that segmentation level.')
    st.altair_chart(depth_chart(current,title,selected,broad if value=='value' else 0,True,interactive=True),
                    width='stretch',key='depth_chart',on_select=select_chart_segment,selection_mode='segment_pick')
    a,b,c=st.columns(3)
    a.metric(f'Broad audience · {outcome_label.lower()} / 10,000',f'{broad:,.1f}')
    b.metric(f'{selected} segments · selected cluster average / 10,000',f'{chosen["value"]*factor:,.1f}')
    c.metric('Selected cluster share',f'{chosen["reach"]:.2f}%')
    c.caption(f'{int(chosen["n"]):,} evaluation users in this cluster')
    st.caption('Averages use every evaluation user in the selected cluster, expressed per 10,000 members. '
               'Cluster sizes differ; the dashed line is the broad-audience average.')
    st.caption('Bars show 95% uncertainty intervals for each estimate, conditional on the fitted clusters and rankings.')
    chosen=current[current.segments==selected].iloc[0]
    chosen_factor=10000
    lower_gain=(chosen['gain']-z*chosen['gain_se'])*chosen_factor
    upper_gain=(chosen['gain']+z*chosen['gain_se'])*chosen_factor
    st.caption('Average advertising response = treatment conversion or visit rate minus control rate within the cluster.')
    if selected==1:
        st.info('The broad-audience strategy provides the reference point for the segmentation comparison.')
    elif lower_gain>0:
        st.success(f'In this dataset, {selected} groups identified a responsive audience covering '
                   f'{chosen["reach"]:.1f}% of users, with an estimated gain of '
                   f'{chosen["gain"]*chosen_factor:,.1f} {outcome_label.lower()} per 10,000 cluster members '
                   'above the broad-audience average.')
    elif upper_gain<0:
        st.warning('This strategy performs worse than random targeting in the evaluation data.')
    else:
        st.info('The gain is uncertain: its interval includes zero.')
    with st.expander('Uncertainty details'):
        st.caption('95% pointwise intervals; gains use paired comparisons with the broad audience.')
        comparison=current[['segments','reach','estimate','lower','upper']].rename(columns={
            'segments':'Segments','reach':'Cluster share (%)','estimate':'Average / 10,000 members',
            'lower':'95% lower','upper':'95% upper'})
        st.dataframe(comparison,hide_index=True,width='stretch')
        st.caption(f'Selected model gain: {chosen["gain"]*chosen_factor:+,.1f} per 10,000 cluster members; '
                   f'95% interval {lower_gain:+,.1f} to {upper_gain:+,.1f}.')

st.divider()
from app.frequency import render_frequency
render_frequency(DATA)

st.divider()
from app.opportunity import render_opportunity
render_opportunity(groups)

from app.ai_assistant import render_ai_mock
render_ai_mock(groups,current,outcome_label,selected)
