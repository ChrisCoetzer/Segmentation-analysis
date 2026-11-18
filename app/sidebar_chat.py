"""Basic sidebar chat; campaign-aware tools and the demo guide come later."""
import os
from pathlib import Path

from dotenv import dotenv_values
import streamlit as st

from src.gemini_chat import ChatError, DEFAULT_MODEL, reply
from src.site_analyst import TOOLS, CAMPAIGN_KEYS, system_context, validate_action
from uuid import uuid4
from app.guided_demo import is_demo_request, start_demo, go_to_step, render_demo_controls, end_demo


def settings():
    local = dotenv_values(Path(__file__).resolve().parents[1] / '.env')
    try:
        secrets = st.secrets
        secret_key = secrets.get('GEMINI_API_KEY', '')
        secret_model = secrets.get('GEMINI_MODEL', '')
    except st.errors.StreamlitSecretNotFoundError:
        secret_key = secret_model = ''
    return (
        (os.getenv('GEMINI_API_KEY') or secret_key or local.get('GEMINI_API_KEY') or '').strip(),
        (os.getenv('GEMINI_MODEL') or secret_model or local.get('GEMINI_MODEL') or DEFAULT_MODEL).strip(),
    )


def render_sidebar_chat(cal):
    api_key, model = settings()
    messages = st.session_state.setdefault('analyst_messages', [])
    with st.sidebar.container(key='analyst_shell'):
        with st.container(key='analyst_header'):
            st.html('<div class="eyebrow">CAMPAIGN RUNWAY</div>')
            st.title('Your analyst')
            status = 'Ready' if api_key else 'Setup needed'
            st.html(f'<span class="pill">Gemini · {status}</span>')
            if messages:
                st.button('Clear chat', key='clear_analyst_chat', on_click=_clear_chat)
            if not api_key:
                st.info('Add GEMINI_API_KEY to the server’s .env file or deployment secrets to enable chat.')
        retry_clicked = False
        history=st.container(height='stretch', border=False, key='analyst_history',autoscroll=True)
        with history:
            if not messages:
                with st.chat_message('assistant'):
                    st.write('Ask about a customer group, chart or campaign result. Enter “give me a demo” to start the guided presentation.')
                if 'demo_step' not in st.session_state:
                    st.button('Give me a demo',key='start_guided_demo',on_click=start_demo,width='stretch')
            for message in messages:
                with st.chat_message(message['role']):
                    st.markdown(message['content'])
                    for action in message.get('actions', []):
                        st.caption('↗ ' + action)
            if st.session_state.get('analyst_error'):
                st.error(st.session_state['analyst_error'])
                retry_clicked = st.button('Retry message',key='retry_analyst_chat')
            render_demo_controls(cal)
        prompt = st.chat_input('Ask your analyst…', disabled=not api_key, key='analyst_prompt', max_chars=8000)
        if retry_clicked:
            prompt = st.session_state['analyst_retry_prompt']
        if prompt:
            user_message = {'role': 'user', 'content': prompt}
            if is_demo_request(prompt):
                messages.extend([user_message,{'role':'assistant','content':'The guided presentation is ready. Use Next and Back to move between steps. Questions can be asked at any point without advancing the presentation.'}])
                start_demo()
                st.rerun()
            changes, actions, navigation = {}, [], []

            def handle_tool(name, args):
                try:
                    update, section, description = validate_action(name, args)
                except (ValueError, TypeError) as exc:
                    return {'ok': False, 'error': str(exc)}
                changes.update(update)
                navigation.append(section)
                actions.append(description)
                return {'ok': True, 'changed_controls': update, 'section': section,
                        'result': description, 'simulation_ran': False}

            # Commit both turns only on success, so failed requests can be retried.
            try:
                with history, st.spinner('Gemini is thinking…'):
                    answer = reply(api_key, messages[-20:] + [user_message], model,
                                   system_instruction=system_context(cal, st.session_state),
                                   tools=TOOLS, tool_handler=handle_tool)
            except ChatError as exc:
                st.session_state['analyst_error'] = str(exc)
                st.session_state['analyst_retry_prompt'] = prompt
                st.rerun()
            else:
                for key, value in changes.items():
                    st.session_state[key] = value
                if any(key in CAMPAIGN_KEYS for key in changes):
                    st.session_state['saved_settings'] = {key: st.session_state[key] for key in CAMPAIGN_KEYS}
                if navigation:
                    st.session_state['analyst_navigation'] = {'section': navigation[-1], 'token': uuid4().hex}
                if 'demo_step' in changes:
                    go_to_step(st.session_state,changes['demo_step'])
                messages.extend([user_message, {'role': 'assistant', 'content': answer, 'actions': actions}])
                st.session_state.pop('analyst_retry_prompt', None)
                st.session_state.pop('analyst_error', None)
                st.rerun()


def _clear_chat():
    if 'demo_step' in st.session_state:
        end_demo()
    st.session_state['analyst_messages'] = []
    st.session_state.pop('analyst_retry_prompt', None)
    st.session_state.pop('analyst_error', None)
