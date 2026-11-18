"""Exercise the detailed tour, questions in context, evidence revisits and fixed example."""
from pathlib import Path
import sys,json
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.guided_demo import STEPS,is_demo_request,example_matches,narration
from src.site_analyst import validate_action
assert is_demo_request('hey, give me a demo!')
assert is_demo_request('give me a demo of the site')
assert not is_demo_request('What does the demo show?')
assert validate_action('start_guided_demo',{})[0]=={'demo_step':0}
app=AppTest.from_file(str(ROOT/'app/streamlit_app.py')).run(timeout=45)
def clean():assert not app.exception,[(e.message,e.stack_trace) for e in app.exception]
def question_reply(key,messages,model,**kwargs):
    evidence=json.loads(kwargs['system_instruction'].split('CURRENT EVIDENCE\n',1)[1])
    guide=evidence['guided_demo']
    assert guide['step_id']==STEPS[app.session_state['demo_step']]['key']
    assert guide['current_explanation']
    assert guide['previous_step']
    return 'This step connects the current visual to the stated campaign decision.'
clean()
with patch('app.sidebar_chat.reply',side_effect=question_reply) as api:
    app.chat_input(key='analyst_prompt').set_value('hey, give me a demo!').run(timeout=45);clean()
    assert not api.called
    assert app.session_state['demo_step']==0
    assert app.button(key='demo_back').disabled
    definitions=set();cards=set();saw_run=False
    for index,s in enumerate(STEPS):
        if index:
            app.button(key='demo_next').click().run(timeout=45);clean()
        assert app.session_state['demo_step']==index
        assert app.session_state['repetition_profile']==s['group']
        assert app.session_state['analyst_navigation']['highlight'] is False
        if s['tab']:assert app.session_state['audience_tab' if s['section']=='audience' else 'exposure_tab']==s['tab']
        if s['day'] is not None:assert app.session_state['response_checkpoint']==s['day']
        if s['tab']=='Customer groups' and s['group']>=0:definitions.add(s['group'])
        if s['conclusion'] is not None:cards.add(s['conclusion'])
        if s['key'] in ['specialist_timing','proof_specialist','example_week']:
            before=(index,app.session_state['audience_tab'],app.session_state['exposure_tab'])
            app.chat_input(key='analyst_prompt').set_value('Why are we looking at this in the demo?').run(timeout=45);clean()
            assert (app.session_state['demo_step'],app.session_state['audience_tab'],app.session_state['exposure_tab'])==before
        if s['kind']=='preset':
            assert app.multiselect(key='focus_groups').value==[3]
            assert app.slider(key='focus_repeat').value==90
            assert app.slider(key='wide_cap').value==1
            assert app.number_input(key='contact_budget').value==250000
            assert 'comparison_run' not in app.session_state
        if s['kind']=='run':
            assert app.button(key='demo_next').disabled
            app.button(key='demo_run_example').click().run(timeout=60);clean()
            assert example_matches(app.session_state['comparison_run'])
            a,b=[int(r['daily'].iloc[-1].ad_responses) for r in app.session_state['comparison_run']['results'].values()]
            assert b-a>=20,(a,b)
            assert not app.button(key='demo_next').disabled
            saw_run=True
        if s['frame'] is not None:
            assert app.session_state['frame_day']==s['frame']
            assert not app.session_state['playing']
    assert definitions==set(range(5)) and cards==set(range(4)) and saw_run
    app.button(key='demo_back').click().run();clean()
    assert app.session_state['demo_step']==len(STEPS)-2
    app.button(key='demo_next').click().run();clean()
    app.button(key='demo_finish').click().run();clean()
    assert 'demo_step' not in app.session_state
    app.button(key='clear_analyst_chat').click().run();clean()
    app.button(key='start_guided_demo').click().run();clean()
    app.button(key='demo_end').click().run();clean()
    assert 'demo_step' not in app.session_state
print(f'{len(STEPS)} steps: five customer definitions, cross-tab evidence, four justified conclusions, example run/checkpoints and contextual Q&A passed.')
