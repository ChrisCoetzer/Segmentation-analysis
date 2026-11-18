"""Verify click selection and Gemini tool actions without external requests."""
import os
import sys
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.gemini_chat import ChatError
os.environ['GEMINI_API_KEY']='test-only-key'

def scripted_reply(key,messages,model,**kwargs):
    prompt=messages[-1]['content']
    if prompt=='Show specialist timing':
        result=kwargs['tool_handler']('show_site_view',{'section':'audience','group':'Specialist enthusiasts','response_day':7})
    else:
        result=kwargs['tool_handler']('set_campaign_controls',{'campaign':'focused','groups':['Specialist enthusiasts'],'contact_cap':6,'repeat_percent':80})
    assert result['ok']
    return 'Applied the requested selection.'

with patch('app.sidebar_chat.reply',side_effect=scripted_reply):
    app=AppTest.from_file(str(ROOT/'app/streamlit_app.py')).run(timeout=45)
    assert not app.exception,app.exception
    app.button(key='choose_audience_3').click().run()
    assert app.session_state['repetition_profile']==3
    assert not any(x.key=='repetition_profile' for x in app.selectbox)
    app.button(key='choose_audience_3').click().run()
    assert app.session_state['repetition_profile']==-1
    app.chat_input(key='analyst_prompt').set_value('Show specialist timing').run(timeout=45)
    assert not app.exception,app.exception
    assert app.session_state['audience_tab']=='Response timing'
    assert app.session_state['response_checkpoint']==7
    assert app.session_state['repetition_profile']==3
    app.chat_input(key='analyst_prompt').set_value('Prepare focused campaign').run(timeout=45)
    assert not app.exception,app.exception
    assert app.multiselect(key='focus_groups').value==[3]
    assert app.slider(key='focus_cap').value==6
    assert app.slider(key='focus_repeat').value==80
    assert 'comparison_run' not in app.session_state
    app.button(key='clear_analyst_chat').click().run()
    assert app.session_state['analyst_messages']==[]
    def failing_reply(key,messages,model,**kwargs):
        kwargs['tool_handler']('set_campaign_controls',{'campaign':'focused','contact_cap':12})
        raise ChatError('Test interruption')
    with patch('app.sidebar_chat.reply',side_effect=failing_reply):
        app.chat_input(key='analyst_prompt').set_value('Change settings').run(timeout=45)
    assert not app.exception,app.exception
    assert app.slider(key='focus_cap').value==6
    assert not app.session_state['analyst_messages']
print('Clickable group selection, linked emphasis, AI tab/timing navigation and draft settings passed.')
