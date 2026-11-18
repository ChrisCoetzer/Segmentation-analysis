"""Same-cohort repetition comparisons: response gained and effort-normalized yield."""
import math
import numpy as np
import pandas as pd
import altair as alt
from src.customer_lab import GROUPS,COLORS
from src.exposure_reference import STAGES
from app.runway_charts import finish

SHORT=[['Household','regulars'],['Bargain','hunters'],['Occasion','shoppers'],['Specialist','enthusiasts'],['Convenience','shoppers']]
PATTERNS=['Early response, small uplift','Strong early response','A reminder often helps','Builds after repeated exposure','Front-loaded response']

def compact(value):
    return f'{value/1000:,.0f}k' if value>=1000 else f'{value:,.0f}'

def response_gain_clusters(stages,selected,row=None,header_only=False):
    viewbox=f'0 {42+row*82} 1120 84' if row is not None else '0 0 1120 42' if header_only else '0 0 1120 480'
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif" viewBox="{viewbox}" role="img" aria-label="Additional modeled responders and advertising contacts at successive exposure stages">']
    for stage,(_,_,label) in enumerate(STAGES if row is None else []):
        x=190+stage*185
        svg.append(f'<text x="{x+85}" y="25" text-anchor="middle" fill="#b4ccd0" font-size="17" font-weight="600">{label} exposure</text>')
    for gid in ([] if header_only else [row] if row is not None else range(5)):
        y=48+gid*82;opacity=1 if selected<0 or gid==selected else .75
        if gid==selected:svg.append(f'<rect x="0" y="{y-4}" width="1115" height="78" rx="14" fill="#1b3435"/>')
        for line,label in enumerate(SHORT[gid]):
            svg.append(f'<text x="10" y="{y+26+line*19}" fill="{COLORS[gid]}" font-size="15" font-weight="600">{label}</text>')
        for _,r in stages[stages.segment_id.eq(gid)].sort_values('stage_id').iterrows():
            x=190+int(r.stage_id)*185
            count=int(math.ceil(float(r.additional_responses)/2))
            svg.append(f'<g opacity="{opacity}">')
            for n in range(count):
                fraction=min(1.,float(r.additional_responses)/2-n)
                svg.append(f'<circle cx="{x+12+(n%12)*5.1:.1f}" cy="{y+13+(n//12)*5.1:.1f}" r="{1.85*math.sqrt(fraction):.2f}" fill="{COLORS[gid]}"/>')
            svg.append(f'<text x="{x+85}" y="{y+32}" fill="{COLORS[gid]}" font-size="24" font-weight="600">+{r.additional_responses:.1f}</text>')
            svg.append(f'<text x="{x+12}" y="{y+64}" fill="#99b3bd" font-size="12">{compact(r.contacts)} ads delivered</text></g>')
        svg.append(f'<line x1="8" x2="1110" y1="{y+76}" y2="{y+76}" stroke="#293e48"/>')
    svg.append('</svg>')
    return ''.join(svg)


def render_repetition_rows(stages,selected):
    import streamlit as st
    from app.audience_selection import select_group,clear_group
    st.image(response_gain_clusters(stages,selected,header_only=True),width='stretch')
    for gid in range(5):
        with st.container(key=f'repetition_group_{gid}'):
            st.image(response_gain_clusters(stages,selected,row=gid),width='stretch')
            st.button(GROUPS[gid],key=f'choose_repetition_{gid}',width='stretch',on_click=select_group,args=(gid,))
    if selected>=0:
        st.button('Show all groups',key='clear_repetition_highlight',on_click=clear_group)

def response_efficiency(stages,selected,repeat_stage='3rd–4th'):
    first=stages[stages.stage_id.eq(0)].set_index('segment_id')
    d=stages[stages.stage.eq(repeat_stage)].copy()
    d['first']=d.segment_id.map(first.responses_per_1000_contacts)*100
    d['repeat']=d.responses_per_1000_contacts*100
    d['first_label']=d['first'].map(lambda v:f'{v:.1f}')
    d['repeat_label']=d['repeat'].map(lambda v:f'{v:.1f}')
    ratio=d['repeat']/d['first']
    d['change']=[f'↑ {r:.1f}×' if r>=1 else f'↓ {(1-r)*100:.0f}%' for r in ratio]
    maximum=float(stages.responses_per_1000_contacts.max())*100
    d['annotation']=maximum*1.17
    colour=alt.Color('profile:N',scale=alt.Scale(domain=GROUPS,range=COLORS),legend=None)
    y=alt.Y('profile:N',sort=GROUPS,title=None,axis=alt.Axis(labelLimit=180))
    tooltip=['profile',alt.Tooltip('first:Q',title='First exposure: responders / 100,000 ads',format='.1f'),alt.Tooltip('repeat:Q',title=f'{repeat_stage}: responders / 100,000 ads',format='.1f'),'change']
    base=alt.Chart(d).encode(y=y,tooltip=tooltip)
    lines=base.mark_rule(strokeWidth=4,opacity=.35).encode(x=alt.X('first:Q',title='Additional responders for the same 100,000 ads',scale=alt.Scale(domain=[0,maximum*1.43],nice=False),axis=alt.Axis(tickCount=6)),x2='repeat:Q',color=colour)
    original=base.mark_point(shape='circle',size=170,filled=True,fill='#0d151c',stroke='#859fa9',strokeWidth=2).encode(x='first:Q')
    repeated=base.mark_circle(size=240,stroke='#0d151c',strokeWidth=2).encode(x='repeat:Q',color=colour,opacity=alt.value(1) if selected<0 else alt.condition(alt.datum.segment_id==selected,alt.value(1),alt.value(.7)))
    labels_first=base.mark_text(dy=-21,fontSize=13,color='#94adb6').encode(x='first:Q',text='first_label:N')
    labels_repeat=base.mark_text(dy=23,fontSize=14,fontWeight=600).encode(x='repeat:Q',text='repeat_label:N',color=colour)
    change=base.mark_text(align='left',fontSize=15,fontWeight=600).encode(x='annotation:Q',text='change:N',color=colour)
    return finish((lines+original+repeated+labels_first+labels_repeat+change).properties(height=390))

def group_summary(detail,stages,selected):
    a=detail[detail.segment_id.eq(selected)].set_index('exposure')
    b=stages[stages.segment_id.eq(selected)].set_index('stage_id')
    first_two=float(a.loc[2,'coverage'])*100
    first=float(b.loc[0,'responses_per_1000_contacts'])
    later=float(b.loc[2,'responses_per_1000_contacts'])
    if selected==3:
        explanation=f'Only {first_two:.0f}% of response potential appears within two exposures. The 3rd–4th exposures add {b.loc[2,"additional_responses"]:.1f} responders, followed by another {b.loc[3,"additional_responses"]:.1f} at exposures 5–8. After accounting for all ads delivered, the 3rd–4th exposures yield {later/first:.1f} times as much response per ad as the first exposure.'
    elif selected==2:
        explanation=f'The second exposure adds more response than the first: {b.loc[1,"additional_responses"]:.1f} versus {b.loc[0,"additional_responses"]:.1f} responders. Later stages add progressively less.'
    elif selected==0:
        explanation=f'{first_two:.0f}% of response potential appears within two exposures, but the overall advertising-associated increase is small. Frequent purchases do not automatically imply a strong response to more advertising.'
    else:
        explanation=f'{first_two:.0f}% of response potential appears within two exposures. The first exposure adds {b.loc[0,"additional_responses"]:.1f} responders; exposures 5–8 together add {b.loc[3,"additional_responses"]:.1f} despite using roughly four times as many ads.'
    return dict(pattern=PATTERNS[selected],first_two=first_two,first_yield=first,later_yield=later,explanation=explanation)
