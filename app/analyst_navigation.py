"""One-shot navigation to fixed application sections; no generated code or selectors."""
import json
import streamlit as st
from src.site_analyst import SECTIONS

TARGETS = {'decision':'.hero-copy',
           'audience_group_0':'.st-key-audience_group_0',
           'audience_panel':'.st-key-audience_tab',
           'timing':'.st-key-audience_tab',
           'repetition_group_3':'.st-key-repetition_group_3',
           'exposure_panel':'.st-key-exposure_tab',
           'campaign_controls':'[data-testid="stForm"]',
           'answer':'.st-key-chapter_answer'}


def install_analyst_navigation():
    # Keep the request mounted across reruns. A fast follow-up chat submission
    # must not remove its iframe before the browser has applied the navigation.
    # The browser token guard makes repeated renders idempotent.
    request = st.session_state.get('analyst_navigation')
    if not request or request.get('section') not in SECTIONS:
        return
    selector = '.st-key-' + SECTIONS[request['section']]
    if request.get('scroll_to')=='playback':selector='.st-key-simulation_playback'
    target = TARGETS.get(request.get('target'),selector)
    st.iframe('''<script>(()=>{
        const host=window.parent,doc=host.document;
        const token=TOKEN,selector=SELECTOR,target=TARGET,persistent=PERSISTENT,clear=CLEAR,highlight=HIGHLIGHT;
        if(host.__analystNavigationToken===token)return;
        if(host.__analystFocusNode){host.__analystFocusNode.classList.remove('demo-focus','analyst-focus');host.__analystFocusNode=null;}
        if(clear){host.__analystNavigationToken=token;return;}
        function go(){
            const node=doc.querySelector(selector),main=doc.querySelector('[data-testid="stMain"]');
            if(!node||!main)return false;
            host.__analystNavigationToken=token;
            const top=node.getBoundingClientRect().top-main.getBoundingClientRect().top+main.scrollTop-64;
            main.scrollTo({top:Math.max(0,top),behavior:host.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
            if(highlight){
                const focus=doc.querySelector(target)||node;
                host.__analystFocusNode=focus;
                focus.classList.remove('analyst-focus','demo-focus');void focus.offsetWidth;
                focus.classList.add(persistent?'demo-focus':'analyst-focus');
                if(!persistent)host.setTimeout(()=>focus.classList.remove('analyst-focus'),3500);
            }
            return true;
        }
        if(!go()){
            const observer=new MutationObserver(()=>{if(go())observer.disconnect()});
            observer.observe(doc.body,{childList:true,subtree:true});
            host.setTimeout(()=>observer.disconnect(),6000);
        }
    })()</script>'''.replace('TOKEN',json.dumps(request['token'])).replace('SELECTOR',json.dumps(selector))
        .replace('TARGET',json.dumps(target)).replace('PERSISTENT',json.dumps(bool(request.get('persistent'))))
        .replace('CLEAR',json.dumps(bool(request.get('clear'))))
        .replace('HIGHLIGHT',json.dumps(request.get('highlight',False))),
        height=1,tab_index=-1,alt='Analyst section navigation')
