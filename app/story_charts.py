"""Presentation-focused visuals and animated customer traces."""
import html
import numpy as np
import pandas as pd
import altair as alt
from src.customer_lab import GROUPS,COLORS
from app.runway_charts import finish

POLICIES=['Focused campaign','Wide-reach campaign']
POLICY_COLORS=['#6aded0','#efb078']

def audience_bars(groups,selected):
    d=groups.copy();d['Share of audience (%)']=d.share*100
    pick=alt.selection_point(name='profile_pick',fields=['segment_id'],on='click',clear=False)
    bars=alt.Chart(d).mark_bar(cornerRadiusEnd=5,height=30).encode(
        x=alt.X('Share of audience (%):Q',title='Share of the customer base (%)',scale=alt.Scale(domain=[0,float(np.ceil(d['Share of audience (%)'].max()/5)*5+5)])),
        y=alt.Y('profile:N',sort=GROUPS,title=None,axis=alt.Axis(labelLimit=160)),
        color=alt.condition(alt.datum.segment_id==selected,alt.value('#6aded0'),alt.value('#334b57')),
        tooltip=['profile',alt.Tooltip('Share of audience (%):Q',format='.2f')]).add_params(pick)
    text=alt.Chart(d).mark_text(align='left',dx=8,color='#e0edeb',fontSize=13).encode(x='Share of audience (%):Q',y=alt.Y('profile:N',sort=GROUPS),text=alt.Text('Share of audience (%):Q',format='.1f'))
    return finish((bars+text).properties(height=280))

def timing_lines(shapes,selected):
    d=shapes.copy();d['Response captured (%)']=100*d.response_share
    return finish(alt.Chart(d).mark_line(strokeWidth=3).encode(
        x=alt.X('day:Q',title='Days after first contact',axis=alt.Axis(values=[1,3,7,10,14])),
        y=alt.Y('Response captured (%):Q',scale=alt.Scale(domain=[0,100])),
        color=alt.Color('profile:N',scale=alt.Scale(domain=GROUPS,range=COLORS)),
        opacity=alt.condition(alt.datum.segment_id==selected,alt.value(1),alt.value(.18)),
        tooltip=['profile','day',alt.Tooltip('Response captured (%):Q',format='.1f')]).properties(height=300))

def contact_lines(frequency,selected):
    d=frequency[(frequency.segment_id==selected)&(frequency.contact_cap<=12)].copy()
    d=pd.concat([pd.DataFrame({'contact_cap':[0],'coverage':[0]}),d],ignore_index=True)
    d['Response paths covered (%)']=d.coverage*100
    return finish(alt.Chart(d).mark_area(color='#6aded0',opacity=.16,line={'color':'#6aded0','strokeWidth':3}).encode(
        x=alt.X('contact_cap:Q',title='Recorded contacts before response',axis=alt.Axis(values=[0,1,3,6,9,12])),
        y=alt.Y('Response paths covered (%):Q',scale=alt.Scale(domain=[0,100])),
        tooltip=[alt.Tooltip('contact_cap:Q',title='Contacts'),alt.Tooltip('Response paths covered (%):Q',format='.1f')]).properties(height=300))

def cumulative_chart(results,day,days,field='ad_responses'):
    data=[]
    for label,r in results.items():
        a=r['daily'][['day',field]].copy();a['campaign']=label
        zero=pd.DataFrame({'day':[0],field:[0],'campaign':[label]})
        data.append(pd.concat([zero,a],ignore_index=True))
    full=pd.concat(data,ignore_index=True);visible=full[full.day<=day]
    maximum=max(5,float(full[field].max())*1.08)
    title='Modeled ad-driven responses' if field=='ad_responses' else 'Unique customers reached'
    lines=alt.Chart(visible).mark_line(strokeWidth=3.5).encode(x=alt.X('day:Q',title='Campaign day',scale=alt.Scale(domain=[0,days]),axis=alt.Axis(values=list(range(0,days+1,7)) or [0,days])),y=alt.Y(field+':Q',title=title,scale=alt.Scale(domain=[0,maximum])),color=alt.Color('campaign:N',scale=alt.Scale(domain=POLICIES,range=POLICY_COLORS)),tooltip=['campaign','day',alt.Tooltip(field+':Q',title=title,format=',')])
    cursor=alt.Chart(pd.DataFrame({'day':[day]})).mark_rule(color='#648592',strokeDash=[3,4]).encode(x='day:Q')
    return finish((lines+cursor).properties(height=295))

def trace_sample(results):
    """Shared, fixed identity sample; responders intentionally represented."""
    n=len(next(iter(results.values()))['customers'])
    responded=np.zeros(n,dtype=bool)
    for r in results.values():responded|=r['customers'].ad_response.to_numpy()|r['customers'].organic_response.to_numpy()
    ids=np.flatnonzero(responded)
    if len(ids)>130:ids=ids[np.linspace(0,len(ids)-1,130).astype(int)]
    other=np.flatnonzero(~responded)
    other=other[np.argsort(np.mod((other+1)*.61803398875,1))[:210]]
    return np.r_[ids,other]

def customer_animation(result,day,indices,color):
    p=result['customers'];cohort=p.arrival_day.to_numpy();h=result['history'];contacts=result['contact_history']
    now=h[day];previous=h[max(0,day-1)]
    count=contacts[day];oldcount=contacts[max(0,day-1)]
    def zone(state,n):return np.where(state==3,2,np.where(state==4,3,np.where(n>0,1,0)))
    z=zone(now,count);oldz=zone(previous,oldcount)
    # Use a different hash from trace selection so sampled nonresponders do
    # not all collect at the left edge of their zone.
    xs=np.array([64.,200.,336.,200.]);jitter=np.mod((indices+1)*.7548776662466927,1)
    jy=np.mod((indices+1)*.41421356237,1)
    entered=cohort<=day
    totals=[int((entered&(z==k)).sum()) for k in range(4)]
    svg=['<style>html,body{margin:0;overflow:hidden;background:transparent}svg{display:block}text{font-family:system-ui,sans-serif;fill:#e0edeb}</style>', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 280" width="100%" role="img" aria-label="Illustrative synthetic customer traces">']
    for i,label in enumerate(['Unreached','Reached','All responses']):
        svg.append(f'<text x="{xs[i]}" y="23" text-anchor="middle" font-size="19">{label}</text><text x="{xs[i]}" y="47" text-anchor="middle" font-size="19" font-weight="600">{totals[i]:,}</text>')
    for x in [132,268]:svg.append(f'<line x1="{x}" y1="63" x2="{x}" y2="205" stroke="#293e48"/>')
    svg.append(f'<text x="200" y="269" text-anchor="middle" font-size="17" fill="#8ea8b3">Inactive · {totals[3]:,}</text>')
    for pos,i in enumerate(indices):
        if not entered[i]:continue
        x=xs[z[i]]+(jitter[pos]-.5)*(340 if z[i]==3 else 110)
        y=221+jy[pos]*24 if z[i]==3 else 72+jy[pos]*125
        oldx=xs[oldz[i]]+(jitter[pos]-.5)*(340 if oldz[i]==3 else 110)
        oldy=221+jy[pos]*24 if oldz[i]==3 else 72+jy[pos]*125
        arriving=cohort[i]==day
        if arriving:oldx=8.;oldy=195.
        fill='#79d4a7' if z[i]==2 else '#617985' if z[i]==3 else color
        touched=count[i]>oldcount[i]
        svg.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{3.5 if touched else 2.7}" fill="{fill}" opacity=".75"><title>Customer {i+1} · {html.escape(GROUPS[int(p.segment_id.iloc[i])])} · {count[i]} contacts</title>')
        if day>0:
            svg.append(f'<animate attributeName="cx" from="{oldx:.2f}" to="{x:.2f}" dur=".55s" fill="freeze"/><animate attributeName="cy" from="{oldy:.2f}" to="{y:.2f}" dur=".55s" fill="freeze"/>')
            if touched:svg.append('<animate attributeName="r" values="5;2.7" dur=".6s" fill="freeze"/>')
        svg.append('</circle>')
    svg.append('</svg>')
    return ''.join(svg)

def scorecard(results,day=None):
    rows=[]
    for label,r in results.items():
        d=r['daily'].iloc[(day or len(r['daily']))-1]
        rows.append({'Campaign':label,'Ad-driven responses':int(d.ad_responses),'Customers reached':int(d.unique_reached),'Contacts used':int(d.cumulative_contacts),'Unused contacts':int(r['scenario']['contact_budget']-d.cumulative_contacts)})
    return pd.DataFrame(rows)
