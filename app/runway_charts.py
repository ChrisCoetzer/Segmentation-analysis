"""Linked chart builders for the customer exploration app."""
import html
import numpy as np
import pandas as pd
import altair as alt
from src.customer_lab import GROUPS,COLORS,STATES

STATE_COLORS=['#94a3b8','#69d1df','#8275bc','#287858','#bd8665','#b49a48','#d7dfe4']
PROFILE_SCALE=alt.Scale(domain=GROUPS,range=COLORS)

def finish(chart):
    return chart.configure(background='#0d151c').configure_view(stroke=None).configure_axis(gridColor='#263a45',domain=False,tickSize=0,labelColor='#a6bac2',titleColor='#a6bac2',labelFontSize=12,titleFontSize=12,titleFontWeight='normal',titlePadding=14).configure_legend(labelFontSize=12,titleFontSize=12,labelColor='#a6bac2',titleColor='#edf4f2',orient='bottom',columns=2,title=None).configure_title(fontSize=15,anchor='start',color='#edf4f2')

def landscape(data,selected):
    pick=alt.selection_point(name='profile_pick',fields=['segment_id'],on='click',clear=False)
    base=alt.Chart(data).encode(x=alt.X('incremental_per_10000:Q',title='Benchmark incremental conversions / 10,000',scale=alt.Scale(zero=True)),y=alt.Y('day80:Q',title='Days to 80% of 14-day responses',scale=alt.Scale(domain=[4.5,10.5])),tooltip=[alt.Tooltip('profile:N',title='Audience'),alt.Tooltip('share_pct:Q',title='Population share (%)',format='.2f'),alt.Tooltip('incremental_per_10000:Q',title='Benchmark increment / 10k',format='.1f'),alt.Tooltip('day80:Q',title='Days to 80%'),alt.Tooltip('n_histories:Q',title='Matched histories',format=',')])
    dots=base.mark_circle(stroke='white',strokeWidth=2).encode(size=alt.Size('share_pct:Q',scale=alt.Scale(range=[180,3600]),legend=None),color=alt.Color('profile:N',scale=PROFILE_SCALE,legend=None),opacity=alt.condition(alt.datum.segment_id==selected,alt.value(1),alt.value(.55))).add_params(pick)
    return finish(dots.properties(height=350))

def response_curve(shapes,selected):
    d=shapes.copy();d['Response observed (%)']=100*d.response_share
    return finish(alt.Chart(d).mark_line(strokeWidth=3,point=True).encode(x=alt.X('day:Q',title='Days since first contact',axis=alt.Axis(tickMinStep=1)),y=alt.Y('Response observed (%):Q',scale=alt.Scale(domain=[0,100])),color=alt.Color('profile:N',scale=PROFILE_SCALE),opacity=alt.condition(alt.datum.segment_id==selected,alt.value(1),alt.value(.15)),tooltip=['profile',alt.Tooltip('day:Q',title='Day'),alt.Tooltip('Response observed (%):Q',format='.1f')]).properties(height=240))

def frequency_curve(freq,selected,cap=6):
    d=freq[(freq.segment_id==selected)&(freq.contact_cap<=20)].copy();d['Coverage (%)']=100*d.coverage
    area=alt.Chart(d).mark_area(color=COLORS[selected],opacity=.18,line={'color':COLORS[selected],'strokeWidth':3}).encode(x=alt.X('contact_cap:Q',title='Recorded contacts before response',axis=alt.Axis(tickMinStep=1)),y=alt.Y('Coverage (%):Q',title='Historical response paths covered (%)',scale=alt.Scale(domain=[0,100])),tooltip=[alt.Tooltip('contact_cap:Q',title='Contacts'),alt.Tooltip('Coverage (%):Q',format='.1f')])
    line=alt.Chart(pd.DataFrame({'contact_cap':[cap]})).mark_rule(color='#edf4f2',strokeDash=[4,4]).encode(x='contact_cap:Q',tooltip=alt.Tooltip('contact_cap:Q',title='Your contact cap'))
    return finish((area+line).properties(height=240))

def cohort_heatmap(data):
    return finish(alt.Chart(data).mark_rect(cornerRadius=2).encode(x=alt.X('day:O',title='Campaign day',axis=alt.Axis(labelAngle=0,labelExpr="datum.value % 7 === 0 || +datum.value === 1 ? datum.label : ''")),y=alt.Y('cohort:N',title=None,sort=['Starting audience','Week 1 arrivals','Week 2 arrivals','Week 3 arrivals','Week 4 arrivals']),color=alt.Color('share:Q',title='Share (%)',scale=alt.Scale(domain=[0,100],range=['#eef3f3','#6aded0'])),tooltip=['cohort',alt.Tooltip('day:Q',title='Day'),alt.Tooltip('customers:Q',format=','),alt.Tooltip('share:Q',title='Share of arrived cohort (%)',format='.1f'),alt.Tooltip('cohort_size:Q',title='Arrived in cohort',format=',')]).properties(height=240))

def arrival_chart(daily):
    d=daily[['day','new_arrivals','returning','departures']].melt('day',var_name='type',value_name='customers')
    d['type']=d.type.map({'new_arrivals':'New arrivals','returning':'Returning','departures':'Leaving active pool'})
    d.loc[d.type=='Leaving active pool','customers']*=-1
    return finish(alt.Chart(d).mark_bar().encode(x=alt.X('day:O',title='Campaign day',axis=alt.Axis(labelAngle=0,labelExpr="datum.value % 7 === 0 || +datum.value === 1 ? datum.label : ''")),y=alt.Y('customers:Q',title='Customers entering / leaving'),color=alt.Color('type:N',scale=alt.Scale(domain=['New arrivals','Returning','Leaving active pool'],range=['#69d1df','#9a8d46','#bd8665'])),tooltip=['type',alt.Tooltip('day:Q',title='Day'),alt.Tooltip('customers:Q',format=',')]).properties(height=245))

def cohort_area(data):
    return finish(alt.Chart(data).mark_area(opacity=.8).encode(x=alt.X('day:Q',title='Campaign day',axis=alt.Axis(tickMinStep=1)),y=alt.Y('customers:Q',title='Active customers',stack='zero'),color=alt.Color('cohort:N',scale=alt.Scale(domain=['Starting audience','Week 1 arrivals','Week 2 arrivals','Week 3 arrivals','Week 4 arrivals'],range=['#8fa5ae','#6aded0','#6b76bb','#b18c56','#4b8669'])),tooltip=['cohort','day',alt.Tooltip('customers:Q',format=',')]).properties(height=230))

def dot_map(result,day,profile=None):
    p=result['customers'];indices=np.arange(len(p))
    if profile is not None:indices=indices[p.segment_id.to_numpy()==profile]
    if len(indices)>900:indices=indices[np.argsort(np.mod((indices+1)*.61803398875,1))[:900]]
    indices=indices[p.arrival_day.to_numpy()[indices]<=day]
    d=p.iloc[indices][['customer_id','profile','cohort']].copy()
    code=result['history'][day,indices]
    d['State']=np.array(STATES)[code]
    d['x']=code+np.mod(d.customer_id.to_numpy()*.6180339,1)*.72-.36
    d['y']=np.mod(d.customer_id.to_numpy()*.4142135,1)
    d['Contacts']=result['contact_history'][day,indices]
    return finish(alt.Chart(d).mark_circle(size=32,opacity=.75).encode(x=alt.X('x:Q',title=None,scale=alt.Scale(domain=[-.65,5.65]),axis=alt.Axis(values=[0,1,2,3,4,5],labelExpr="['New','Engaged','Ready','Responded','Inactive','Returning'][datum.value]",grid=False)),y=alt.Y('y:Q',axis=None,title=None),color=alt.Color('profile:N',scale=PROFILE_SCALE),tooltip=[alt.Tooltip('customer_id:Q',title='Synthetic customer'),'profile','State','cohort','Contacts']).properties(height=360))

def comparison_chart(data,field,label):
    return finish(alt.Chart(data).mark_line(strokeWidth=3).encode(x=alt.X('day:Q',title='Campaign day',axis=alt.Axis(tickMinStep=1)),y=alt.Y(field+':Q',title=label),color=alt.Color('strategy:N',scale=alt.Scale(domain=['Your scenario','Broad reach','Focused repeats','Balanced'],range=['#6aded0','#8698a0','#b2764d','#8177b5'])),strokeDash=alt.condition(alt.datum.strategy=='Your scenario',alt.value([1,0]),alt.value([5,3])),tooltip=['strategy','day',alt.Tooltip(field+':Q',title=label,format=',')]).properties(height=310))

def sankey_svg(result,day,profile=None):
    """Three snapshots, with exact identity-conserving flows between snapshots."""
    times=[0,max(1,day//2),day]
    mask=np.ones(len(result['customers']),dtype=bool) if profile is None else result['customers'].segment_id.eq(profile).to_numpy()
    states=result['history'][:,mask];total=mask.sum()
    w,h=1100,440;xs=[25,410,795];nodew=12;gap=11;top=42
    positions=[];heights=[]
    for t in times:
        counts=np.bincount(states[t],minlength=7)
        nonzero=np.count_nonzero(counts)
        usable=h-top-20-gap*(nonzero-1)
        heights0=np.where(counts>0,np.maximum(7,counts/max(1,total)*usable),0)
        # Renormalize the nonzero heights so every column fits exactly.
        heights0*=usable/max(1,heights0.sum())
        yy=[];cursor=top
        for size in heights0:
            yy.append(cursor)
            if size:cursor+=size+gap
        positions.append(yy);heights.append(heights0)
    svg=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Synthetic customer flows between day zero, midpoint and selected day"><style>text{{font-family:system-ui,sans-serif;fill:#294450;font-size:16px}}</style>']
    for col in range(2):
        matrix=np.bincount(states[times[col]].astype(int)*7+states[times[col+1]],minlength=49).reshape(7,7)
        counts0=matrix.sum(axis=1);counts1=matrix.sum(axis=0)
        sourceoff=np.zeros(7);targetoff=np.zeros(7)
        for fr in range(7):
            for to in range(7):
                value=matrix[fr,to]
                if not value:continue
                hs=heights[col][fr]*value/counts0[fr];ht=heights[col+1][to]*value/counts1[to]
                y0=positions[col][fr]+sourceoff[fr];y1=positions[col+1][to]+targetoff[to]
                x0=xs[col]+nodew;x1=xs[col+1];mid=(x0+x1)/2
                path=f'M{x0},{y0} C{mid},{y0} {mid},{y1} {x1},{y1} L{x1},{y1+ht} C{mid},{y1+ht} {mid},{y0+hs} {x0},{y0+hs} Z'
                svg.append(f'<path d="{path}" fill="{STATE_COLORS[fr]}" opacity=".24"><title>{html.escape(STATES[fr])} to {html.escape(STATES[to])}: {value:,} customers</title></path>')
                sourceoff[fr]+=hs;targetoff[to]+=ht
    for col,t in enumerate(times):
        svg.append(f'<text x="{xs[col]}" y="20" style="font-weight:600">Day {t}</text>')
        counts=np.bincount(states[t],minlength=7)
        for code in np.flatnonzero(counts):
            y=positions[col][code];size=heights[col][code]
            name='Arriving later' if code==6 else STATES[code]
            svg.append(f'<rect x="{xs[col]}" y="{y}" width="{nodew}" height="{size}" fill="{STATE_COLORS[code]}" rx="2"/>')
            svg.append(f'<text x="{xs[col]+nodew+6}" y="{y+max(5,size/2)+4}">{html.escape(name)} · {counts[code]:,}</text>')
    svg.append('</svg>')
    return ''.join(svg)
