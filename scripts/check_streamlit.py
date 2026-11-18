"""Exercise real app controls against the exported result tables."""
from pathlib import Path
import sys

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
app=AppTest.from_file(str(ROOT/'app/legacy_app.py')).run(timeout=45)
assert not app.exception,app.exception
assert all(h.value!='Explore the segmentation groups' for h in app.header)
assert all(s.key!='evaluation' for s in app.selectbox)
assert app.radio(key='outcome').value=='Conversions'
groups=pd.read_parquet(ROOT/'app/data/groups.parquet')
groups=groups[groups.segments<=32]
assert all(r.key!='outcome' for r in app.sidebar.radio)
assert all(s.key!='segments' for s in app.sidebar.select_slider)
import json
assert 'Feature-only' in json.loads((ROOT/'app/data/run.json').read_text())['method']
shared=['segments','group','node','n','treated','control','share','evaluation']
pd.testing.assert_frame_equal(groups[groups.outcome=='conversion'][shared].reset_index(drop=True),
                              groups[groups.outcome=='visit'][shared].reset_index(drop=True))

assert all(s.key not in ['reach','investment_transfer'] for s in app.slider)
assert len(app.get('vega_lite_chart'))==3
from src.segmentation import cluster_average_comparison
expected=cluster_average_comparison(groups,'conversion')
main=app.dataframe[0].value
assert ((main['Average / 10,000 members'].to_numpy()-expected['value'].to_numpy()*10000)**2).max()<1e-16
from src.investment import population_investment_scenario
expected_scenario=population_investment_scenario(groups,100000,12.5,10,100)
assert all(e.label!='Calculation and scenario data' for e in app.expander)
assert all(b.label!='Download break-even scenario' for b in app.button)
for row in expected_scenario[expected_scenario.segments>1].itertuples():
    assert next(m.value for m in app.metric if m.label==f'{row.segments} groups · break-even spend')==f'${row.break_even_cost:,.0f}'
default_value=app.metric[0].value
app.radio(key='outcome').set_value('Visits').run()
assert not app.exception,app.exception
assert app.metric[0].value!=default_value
app.session_state['segments']=32
app.run()
app.radio(key='measure').set_value('Gain over broad targeting').run()
assert not app.exception,app.exception
app.radio(key='outcome').set_value('Conversions').run()
expected=cluster_average_comparison(groups,'conversion')
assert ((app.dataframe[0].value['Average / 10,000 members'].to_numpy()-expected.gain.to_numpy()*10000)**2).max()<1e-16
assert len(app.get('vega_lite_chart'))==3
assert all(e.label!='Frequency data, definitions, and limits' for e in app.expander)
assert 'Observed pair conversion rate'==app.metric[5].label
pooled=app.metric[3].value
campaign_options=app.selectbox(key='campaign').options
counts=pd.read_parquet(ROOT/'app/data/frequency.parquet')
largest=counts.groupby('campaign').pairs.sum().idxmax()
app.selectbox(key='campaign').set_value(largest).run()
assert not app.exception,app.exception
assert app.metric[3].value!=pooled
app.multiselect(key='frequency_bins').set_value(['1','11+']).run()
app.radio(key='frequency_measure').set_value('Audience distribution').run()
assert not app.exception,app.exception
assert len(app.get('vega_lite_chart'))==3
assert all(n.key!='frequency_minimum' for n in app.number_input)
assert all(e.label!='Refine the frequency groups' for e in app.expander)
app.multiselect(key='frequency_bins').set_value([]).run()
assert not app.exception,app.exception
assert app.warning
assert len(app.get('vega_lite_chart'))==2
assert counts.impressions.sum()==16468027
assert counts.pairs.sum()==7813401
app.radio(key='outcome').set_value('Conversions').run()
app.session_state['segments']=32
app.run()
assert not app.exception,app.exception
assert '32 segments' in app.metric[1].label
assert all(s.key!='segments' for s in app.select_slider)
assert expected.segments.tolist()==[1,2,4,8,16,32]
app.number_input(key='investment_population').set_value(0).run()
assert not app.exception,app.exception
def scenario_metric(label):
    return next(m.value for m in app.metric if m.label==label)
assert all(scenario_metric(f'{k} groups · break-even spend')=='$0' for k in [2,4,8,16,32])
assert all(not (n.key or '').startswith('investment_cost_') for n in app.number_input)
app.number_input(key='investment_population').set_value(125000).run()
app.number_input(key='investment_baseline').set_value(0.).run()
assert not app.exception,app.exception
assert all(scenario_metric(f'{k} groups · break-even spend')=='$0' for k in [2,4,8,16,32])
app.number_input(key='investment_baseline').set_value(10.).run()
assert not app.exception,app.exception
before=[scenario_metric(f'{k} groups · break-even spend') for k in [2,4,8,16,32]]
assert all(v!='$0' for v in before)
app.radio(key='outcome').set_value('Visits').run()
assert not app.exception,app.exception
assert before==[scenario_metric(f'{k} groups · break-even spend') for k in [2,4,8,16,32]]
app.slider(key='investment_reach').set_value(25.).run()
assert not app.exception,app.exception
assert scenario_metric('Customers selected')=='31,250'
app.slider(key='investment_reach').set_value(100.).run()
assert not app.exception,app.exception
assert all(scenario_metric(f'{k} groups · break-even spend')=='$0' for k in [2,4,8,16,32])
app.slider(key='investment_reach').set_value(0.).run()
assert not app.exception,app.exception
assert scenario_metric('Customers selected')=='0'
for i in [1,2,0]:
    app.button(key=f'ai_suggestion_{i}').click().run()
    assert not app.exception,app.exception
    assert len(app.sidebar.chat_message)==2
assert 'summary' in app.session_state['ai_question']
assert any('MOCKUP' in c.value for c in app.sidebar.caption)
assert len(app.sidebar.chat_message)==2
print('App controls and exported policy invariants passed.')
