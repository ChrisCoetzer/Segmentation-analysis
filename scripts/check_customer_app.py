"""Verify the continuous story, AI-only sidebar and campaign playback."""
from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
app=AppTest.from_file(str(ROOT/'app/streamlit_app.py')).run(timeout=45)
def clean():
    assert not app.exception,[(x.message,x.stack_trace) for x in app.exception]
    assert len(app.sidebar.slider)==0 and len(app.sidebar.number_input)==0
    assert len(app.sidebar.selectbox)==0 and len(app.sidebar.multiselect)==0
clean()
titles=[x.value for x in app.title]
assert 'Meet the audience' in titles
assert 'Where does repetition keep finding customers?' in titles
assert 'Build two campaigns. Watch what happens.' in titles
assert 'Who should receive the next ad?' in titles
assert not any(x.key=='story_step' for x in app.get('button_group'))
assert not any(x.key in ['story_next','story_back'] for x in app.button)
assert not app.dataframe
assert [tab.label for tab in app.tabs]==['Customer groups','Shopping differences','Conversion rates','Response timing','What each stage adds','What we learned']
assert not any(x.key=='selected_profile' for x in app.selectbox)
app.select_slider(key='response_checkpoint').set_value(1).run();clean()
app.button(key='choose_repetition_3').click().run();clean()
app.select_slider(key='response_checkpoint').set_value(30).run();clean()
app.button(key='choose_repetition_4').click().run();clean()
assert not any(x.key=='effort_stage' for x in app.get('button_group'))
app.button(key='clear_repetition_highlight').click().run();clean()
assert not any('Response potential reached in first 2 exposures' in x.label for x in app.metric)
assert not any(x.key=='response_units' for x in app.get('button_group'))
app.selectbox(key='initial_population').set_value(25000)
app.multiselect(key='focus_groups').set_value([3,4])
app.slider(key='focus_cap').set_value(4)
app.button(key='run_comparison').click().run(timeout=45);clean()
app.button(key='play_pause').click().run();clean()
assert not app.session_state['playing']
day=app.session_state['frame_day']
app.button(key='play_next').click().run();clean()
assert app.session_state['frame_day']==day+1
app.button(key='play_final').click().run();clean()
assert app.session_state['frame_day']==30
assert all(len(x.value)==2 for x in app.dataframe if 'Ad-driven responses' in x.value.columns)
run=app.session_state['comparison_run'];a,b=run['results'].values()
assert a['customers'].customer_id.equals(b['customers'].customer_id)
assert a['scenario']['contact_budget']==b['scenario']['contact_budget']
assert a['scenario']['eligible_profiles']==(3,4)
assert a['scenario']['population_profiles']==tuple(range(5))
pd.testing.assert_frame_equal(a['customers'][['customer_id','source_row_index','segment_id','arrival_day']],b['customers'][['customer_id','source_row_index','segment_id','arrival_day']])
assert app.slider(key='focus_cap').value==4
app.multiselect(key='focus_groups').set_value([3])
app.multiselect(key='wide_groups').set_value([3])
app.button(key='run_comparison').click().run(timeout=45);clean()
app.button(key='play_final').click().run();clean()
for result in app.session_state['comparison_run']['results'].values():
    assert result['scenario']['population_profiles']==(3,)
    assert result['customers'].segment_id.eq(3).all()
    assert result['customers'].arrival_day.eq(0).sum()==25000
app.slider(key='turnover_rate').set_value(40)
app.number_input(key='contact_budget').set_value(0)
app.button(key='run_comparison').click().run(timeout=45);clean()
app.button(key='play_final').click().run();clean()
assert all((x.value['Ad-driven responses']==0).all() for x in app.dataframe if 'Ad-driven responses' in x.value.columns)
app.multiselect(key='focus_groups').set_value([])
app.button(key='run_comparison').click().run();clean()
assert app.error
print('All chapters render together; AI-only sidebar, campaign settings, playback, linked results, and zero-budget checks passed.')
