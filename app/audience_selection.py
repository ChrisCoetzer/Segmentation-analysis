"""Clickable group names alongside ranked audience bars and membership rules."""
import html
import streamlit as st
from src.customer_lab import GROUPS, COLORS
from src.retail_metadata import GROUP_RULES


def select_group(gid):
    st.session_state['repetition_profile'] = -1 if st.session_state.get('repetition_profile') == gid else gid


def clear_group():
    st.session_state['repetition_profile'] = -1


def render_audience_selection(cal):
    selected = st.session_state.get('repetition_profile', -1)
    missions = {p['segment_id']: p['mission'] for p in cal['catalogue']}
    a,b,c = st.columns([2.5,3.5,4])
    a.caption('CUSTOMER GROUP · CLICK TO HIGHLIGHT')
    b.caption('SHARE OF ALL CUSTOMERS')
    c.caption('HOW WE IDENTIFY THEM')
    for rank,(_,g) in enumerate(cal['groups'].sort_values('share',ascending=False).iterrows()):
        gid = int(g.segment_id)
        color = COLORS[gid]
        with st.container(key=f'audience_group_{gid}'):
            a,b,c = st.columns([2.5,3.5,4], vertical_alignment='center')
            with a:
                st.html(f'<div class="group-name">{html.escape(GROUPS[gid])}</div>')
                st.html(f'<div class="group-mission">{html.escape(missions[gid])}</div>')
            with b:
                share = float(g.share)*100
                st.html(f'<div class="audience-share"><div class="audience-track"><span style="width:{share/35*100:.2f}%;background:{color}"></span></div><strong style="color:{color}">{share:.0f}%</strong></div>'
                        + ('<div class="group-mission">Largest customer group</div>' if rank == 0 else ''))
            with c:
                st.html(f'<div class="group-criteria">{html.escape(GROUP_RULES[gid])}</div>')
            st.button(GROUPS[gid], key=f'choose_audience_{gid}', width='stretch',
                      on_click=select_group, args=(gid,))
    if selected >= 0:
        st.button('Show all groups', key='clear_audience_highlight', on_click=clear_group)
        st.caption(f'{GROUPS[selected]} highlighted here and in the continued-exposure chart. Campaign eligibility stays separate.')
        st.html(f'<style>.st-key-audience_group_{selected}{{border-color:{COLORS[selected]}!important;box-shadow:inset 4px 0 {COLORS[selected]};background:#1b3435!important}}</style>')
