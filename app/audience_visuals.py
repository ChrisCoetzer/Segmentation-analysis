"""Customer comparison views: countable people, shopping space, decision paths."""
import html
import textwrap
import numpy as np
import pandas as pd
import altair as alt
from src.customer_lab import GROUPS,COLORS
from src.retail_metadata import GROUP_RULES
from app.runway_charts import finish

SHORT=['Household<br>regulars','Bargain<br>hunters','Occasion<br>shoppers','Specialist<br>enthusiasts','Convenience<br>shoppers']
SCALE=alt.Scale(domain=GROUPS,range=COLORS)

def audience_overview(groups,catalogue):
    """Ranked population shares and selection rules, all visible together."""
    missions={p['segment_id']:p['mission'] for p in catalogue}
    svg=['<svg xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif" viewBox="0 0 1200 520" role="img" aria-label="All five customer groups ranked by population share, alongside their shopping mission and selection criteria">']
    for x,label in [(18,'CUSTOMER GROUP'),(290,'SHARE OF CUSTOMERS'),(740,'HOW WE IDENTIFY THEM')]:
        svg.append(f'<text x="{x}" y="22" fill="#9bb4bd" font-size="12" font-weight="600" letter-spacing="1">{label}</text>')
    for value in [0,10,20,30]:
        x=290+value*10
        svg.append(f'<text x="{x}" y="51" text-anchor="middle" font-size="11" fill="#8da7b2">{value}%</text>')
    ordered=groups.sort_values('share',ascending=False)
    for rank,(_,g) in enumerate(ordered.iterrows()):
        gid=int(g.segment_id);y=69+rank*87;share=float(g.share)*100
        svg.append(f'<rect x="0" y="{y}" width="1195" height="78" rx="12" fill="{"#1b3435" if rank==0 else "#14232d"}"/>')
        svg.append(f'<rect x="0" y="{y+11}" width="4" height="56" rx="2" fill="{COLORS[gid]}"/>')
        svg.append(f'<text x="18" y="{y+29}" font-size="17" font-weight="600" fill="#e0edeb">{html.escape(GROUPS[gid])}</text>')
        for line,label in enumerate(textwrap.wrap(missions[gid],width=33)):
            svg.append(f'<text x="18" y="{y+49+line*15}" font-size="12" fill="#a0b8bd">{html.escape(label)}</text>')
        svg.append(f'<rect x="290" y="{y+23}" width="{share*10:.1f}" height="23" rx="5" fill="{COLORS[gid]}"/>')
        svg.append(f'<text x="{306+share*10:.1f}" y="{y+43}" font-size="25" font-weight="600" fill="{COLORS[gid]}">{share:.0f}%</text>')
        if rank==0:svg.append(f'<text x="290" y="{y+65}" font-size="12" font-weight="600" fill="#8bd9b7">Largest customer group</text>')
        for line,label in enumerate(textwrap.wrap(GROUP_RULES[gid],width=56)):
            svg.append(f'<text x="740" y="{y+27+line*20}" font-size="14" fill="#b4ccd0">{html.escape(label)}</text>')
    svg.append('</svg>')
    return ''.join(svg)

def population_mosaic(groups,selected):
    shares=groups.sort_values('segment_id').share.to_numpy()*100
    counts=np.floor(shares).astype(int)
    counts[np.argsort(-(shares-counts))[:100-counts.sum()]]+=1
    group=np.repeat(np.arange(5),counts)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif" viewBox="0 0 660 410" role="img" aria-label="One hundred people representing the customer mix">']
    for n,gid in enumerate(group):
        x=24+(n%20)*30;y=20+(n//20)*47
        fill=COLORS[gid];opacity=1 if gid==selected else .30
        svg.append(f'<g fill="{fill}" opacity="{opacity}"><title>{html.escape(GROUPS[gid])}</title><circle cx="{x}" cy="{y}" r="5"/><rect x="{x-6}" y="{y+8}" width="12" height="18" rx="5"/></g>')
    for gid in range(5):
        x=10+(gid%3)*215;y=300+(gid//3)*58
        svg.append(f'<circle cx="{x+5}" cy="{y}" r="5" fill="{COLORS[gid]}"/><text x="{x+18}" y="{y+4}" fill="#d3e8e4" font-size="12">{html.escape(GROUPS[gid])}</text><text x="{x+18}" y="{y+23}" fill="#d3e8e4" font-size="14" font-weight="600">{counts[gid]} of every 100</text>')
    svg.append('</svg>')
    return ''.join(svg)

def customer_card(persona,group):
    gid=int(persona['segment_id']);color=COLORS[gid]
    return f'''<div class="customer-card" style="--group-color:{color}">
      <div class="customer-quote">“{html.escape(persona['quote'])}”</div>
      <div class="customer-mission">{html.escape(persona['product_examples'])}</div>
      <div class="customer-stats"><div><b>{group.share*100:.0f}%</b><span>of the audience</span></div>
      <div><b>{persona['orders_median']:.0f}</b><span>orders / year</span></div>
      <div><b>${persona['basket_median']:.0f}</b><span>typical basket</span></div></div>
      <div class="group-rule"><span>HOW WE IDENTIFY THEM</span>{html.escape(GROUP_RULES[gid])}</div>
    </div>'''

def shopping_averages(templates,field,selected=-1):
    """One mean per customer group; all profiles, equally weighted."""
    d=templates.groupby('segment_id',as_index=False)[field].mean().rename(columns={field:'average'})
    d['profile']=d.segment_id.map(dict(enumerate(GROUPS)))
    basket=field=='typical_basket'
    title='Average basket size ($)' if basket else 'Average purchases per customer / year'
    d['label']=d.average.map(lambda x:f'${x:,.0f}' if basket else f'{x:.1f}')
    bars=alt.Chart(d).mark_bar(height=32,cornerRadiusEnd=4).encode(
        x=alt.X('average:Q',title=title,scale=alt.Scale(domain=[0,float(d.average.max())*1.22],nice=False),axis=alt.Axis(format='$,.0f' if basket else '.0f',tickCount=5)),
        y=alt.Y('profile:N',sort=GROUPS,title=None,axis=alt.Axis(labelLimit=180)),
        color=alt.Color('profile:N',scale=SCALE,legend=None),
        tooltip=['profile',alt.Tooltip('average:Q',title=title,format='$,.2f' if basket else '.2f')])
    labels=alt.Chart(d).mark_text(align='left',dx=8,fontSize=14,fontWeight=600,color='#e0edeb').encode(
        x='average:Q',y=alt.Y('profile:N',sort=GROUPS),text='label:N')
    if selected>=0:
        emphasis=alt.condition(alt.datum.segment_id==selected,alt.value(1),alt.value(.25))
        bars=bars.encode(opacity=emphasis);labels=labels.encode(opacity=emphasis)
    return finish((bars+labels).properties(height=280))

def promotion_ranges(templates):
    rows=[]
    for gid,a in templates.groupby('segment_id'):
        lo,med,hi=np.quantile(a.promotion_affinity,[.1,.5,.9])*100
        rows.append(dict(profile=GROUPS[gid],low=lo,median=med,high=hi,label=f'{med:.0f}%'))
    d=pd.DataFrame(rows)
    enc=dict(y=alt.Y('profile:N',sort=GROUPS,title=None,axis=alt.Axis(labelLimit=180)),color=alt.Color('profile:N',scale=SCALE,legend=None))
    ranges=alt.Chart(d).mark_rule(strokeWidth=12,opacity=.20).encode(x=alt.X('low:Q',title='Promotion preference (%)',scale=alt.Scale(domain=[0,100])),x2='high:Q',**enc)
    dots=alt.Chart(d).mark_circle(size=170).encode(x='median:Q',**enc,tooltip=['profile',alt.Tooltip('low:Q',title='10th percentile',format='.0f'),alt.Tooltip('median:Q',title='Median',format='.0f'),alt.Tooltip('high:Q',title='90th percentile',format='.0f')])
    labels=alt.Chart(d).mark_text(dx=15,align='left',fontSize=14,fontWeight=600,color='#edf4f2').encode(x='median:Q',y=alt.Y('profile:N',sort=GROUPS),text='label:N')
    return finish((ranges+dots+labels).properties(height=320))

def response_tiles(shapes,day,selected=-1):
    d=shapes.query('day==@day').sort_values('segment_id')
    svg=['<svg xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif" viewBox="0 0 1100 370" role="img" aria-label="Response captured by the selected day, out of one hundred eventual responders in each customer group">']
    for col,(_,row) in enumerate(d.iterrows()):
        gid=int(row.segment_id);x=col*220;share=float(row.response_share);filled=round(share*100)
        opacity=1 if selected<0 or selected==gid else .4
        svg.append(f'<g opacity="{opacity}">')
        svg.append(f'<rect x="{x+2}" y="2" width="210" height="356" rx="16" fill="#15262f" stroke="{COLORS[gid] if selected==gid else "#20353f"}" stroke-width="{2 if selected==gid else 1}"/>')
        for i,line in enumerate(SHORT[gid].split('<br>')):
            svg.append(f'<text x="{x+20}" y="{30+i*20}" fill="#e0edeb" font-size="16" font-weight="600">{line}</text>')
        svg.append(f'<text x="{x+20}" y="102" fill="{COLORS[gid]}" font-size="36" font-weight="600">{share*100:.0f}%</text>')
        for n in range(100):
            cx=x+24+(n%10)*17;cy=128+(n//10)*17
            fill=COLORS[gid] if n<filled else '#2b414b'
            svg.append(f'<circle cx="{cx}" cy="{cy}" r="5.4" fill="{fill}"/>')
        svg.append(f'<text x="{x+20}" y="326" fill="#a0bac1" font-size="13">{100-share*100:.0f}% still to come</text>')
        svg.append('</g>')
    svg.append('</svg>')
    return ''.join(svg)

def advertising_comparison(groups,units='Per 10,000 customers',selected=-1):
    """Matched treatment/control rates on one axis; no simulated campaign."""
    d=groups.copy();factor=100 if units=='Conversion rate (%)' else 10000
    d['without']=d.baseline_rate*factor
    d['with']= (d.baseline_rate+d.incremental_rate)*factor
    d['difference']=d.incremental_rate*factor
    d['without_label']=d['without'].map(lambda x:f'{x:.2f}%' if factor==100 else f'{x:.1f}')
    d['with_label']=d['with'].map(lambda x:f'{x:.2f}%' if factor==100 else f'{x:.1f}')
    y=alt.Y('profile:N',sort=GROUPS,title=None,axis=alt.Axis(labelLimit=180))
    title='Customers who buy per 10,000' if factor==10000 else 'Conversion rate (%)'
    enc=dict(y=y,tooltip=['profile',alt.Tooltip('without:Q',title='Without advertising',format='.3f' if factor==100 else '.1f'),alt.Tooltip('with:Q',title='With advertising',format='.3f' if factor==100 else '.1f'),alt.Tooltip('difference:Q',title='Difference (percentage points)' if factor==100 else 'Extra buyers / 10,000',format='.3f' if factor==100 else '.1f')])
    lines=alt.Chart(d).mark_rule(strokeWidth=5,opacity=.35).encode(x=alt.X('without:Q',title=title,scale=alt.Scale(domain=[0,float(d['with'].max())*1.17],nice=False),axis=alt.Axis(tickCount=6,format='.1f' if factor==100 else '.0f')),x2='with:Q',color=alt.Color('profile:N',scale=SCALE,legend=None),**enc)
    control=alt.Chart(d).mark_circle(size=200,color='#aebbb7',opacity=1,stroke='#0d151c',strokeWidth=2).encode(x='without:Q',**enc)
    treated=alt.Chart(d).mark_circle(size=300,opacity=1,stroke='#0d151c',strokeWidth=2).encode(x='with:Q',color=alt.Color('profile:N',scale=SCALE,legend=None),**enc)
    low=alt.Chart(d).mark_text(dy=21,fontSize=13,color='#97afb8').encode(x='without:Q',y=y,text='without_label:N')
    high=alt.Chart(d).mark_text(dy=-23,fontSize=15,fontWeight=600).encode(x='with:Q',y=y,text='with_label:N',color=alt.Color('profile:N',scale=SCALE,legend=None))
    if selected>=0:
        emphasis=alt.condition(alt.datum.segment_id==selected,alt.value(1),alt.value(.25))
        lines,control,treated,low,high=[chart.encode(opacity=emphasis) for chart in [lines,control,treated,low,high]]
    return finish((lines+control+treated+low+high).properties(height=315))

EXPOSURE_BUCKETS=['1 ad','2 ads','3–4 ads','5+ ads']

def exposure_distribution(frequency):
    rows=[]
    for gid,a in frequency.groupby('segment_id'):
        a=a.sort_values('contact_cap')
        cumulative=np.interp([1,2,4],np.r_[0,a.contact_cap],np.r_[0,a.coverage])
        shares=np.maximum(0,np.diff(np.r_[0,cumulative,1]))
        for bucket,share in zip(EXPOSURE_BUCKETS,shares):
            rows.append(dict(segment_id=gid,profile=GROUPS[gid],bucket=bucket,share=float(share)))
    return pd.DataFrame(rows)

def exposure_swarms(frequency,highlight='All exposures'):
    """100 countable responder dots per row, split by pre-response exposures."""
    d=exposure_distribution(frequency)
    svg=['<svg xmlns="http://www.w3.org/2000/svg" font-family="system-ui,sans-serif" viewBox="0 0 1100 580" role="img" aria-label="Responders grouped by how many advertising exposures preceded their response">']
    for b,label in enumerate(EXPOSURE_BUCKETS):
        x=205+b*220;active=highlight=='All exposures' or highlight==label
        if highlight==label:svg.append(f'<rect x="{x}" y="0" width="215" height="570" rx="14" fill="#1b3435"/>')
        svg.append(f'<text x="{x+105}" y="30" text-anchor="middle" fill="{"#6aded0" if active else "#78909a"}" font-size="18" font-weight="600">{label}</text>')
    for gid in range(5):
        y=68+gid*99
        for line,label in enumerate(SHORT[gid].split('<br>')):
            svg.append(f'<text x="8" y="{y+22+line*20}" fill="{COLORS[gid]}" font-size="16" font-weight="600">{label}</text>')
        shares=d[d.segment_id.eq(gid)].share.to_numpy()*100
        counts=np.floor(shares).astype(int);counts[np.argsort(-(shares-counts))[:100-counts.sum()]]+=1
        for b,(share,count) in enumerate(zip(shares,counts)):
            x=205+b*220;active=highlight=='All exposures' or highlight==EXPOSURE_BUCKETS[b]
            opacity=1 if active else .17
            svg.append(f'<g opacity="{opacity}">')
            for n in range(count):
                cx=x+24+(n%10)*8;cy=y+9+(n//10)*8
                svg.append(f'<circle cx="{cx}" cy="{cy}" r="2.9" fill="{COLORS[gid]}"/>')
            svg.append(f'<text x="{x+119}" y="{y+33}" fill="{COLORS[gid]}" font-size="25" font-weight="600">{share:.0f}%</text></g>')
        svg.append(f'<line x1="0" y1="{y+80}" x2="1090" y2="{y+80}" stroke="#e0e8e0"/>')
    svg.append('</svg>')
    return ''.join(svg)

def response_windows(shapes):
    rows=[]
    for gid,a in shapes.groupby('segment_id'):
        a=a.set_index('day').response_share;start=0
        for order,(day,label) in enumerate([(1,'Day 1'),(3,'Days 2–3'),(7,'Days 4–7'),(14,'Days 8–14')]):
            end=float(a.loc[day])*100
            rows.append(dict(profile=GROUPS[gid],window=label,start=start,end=end,mid=(start+end)/2,share=end-start,order=order,label=f'{end-start:.0f}%' if end-start>=8 else ''))
            start=end
    d=pd.DataFrame(rows);colors=alt.Scale(domain=['Day 1','Days 2–3','Days 4–7','Days 8–14'],range=['#6aded0','#63a8a4','#c5ad70','#c47c54'])
    bars=alt.Chart(d).mark_bar(height=32,cornerRadius=2).encode(x=alt.X('start:Q',title='Share of 30-day responses (%)',scale=alt.Scale(domain=[0,100])),x2='end:Q',y=alt.Y('profile:N',sort=GROUPS,title=None,axis=alt.Axis(labelLimit=180)),color=alt.Color('window:N',scale=colors),tooltip=['profile','window',alt.Tooltip('share:Q',title='Responses (%)',format='.1f')])
    text=alt.Chart(d).mark_text(color='white',fontWeight=600,fontSize=12).encode(x='mid:Q',y=alt.Y('profile:N',sort=GROUPS),text='label:N')
    return finish((bars+text).properties(height=230))

def cap_coverage(frequency,cap):
    rows=[]
    for gid,a in frequency.groupby('segment_id'):
        covered=100*float(np.interp(cap,np.r_[0,a.contact_cap],np.r_[0,a.coverage]))
        rows.append(dict(profile=GROUPS[gid],coverage=covered,remainder=100-covered,label=f'{covered:.0f}%',end=100))
    d=pd.DataFrame(rows)
    enc=dict(y=alt.Y('profile:N',sort=GROUPS,title=None,axis=alt.Axis(labelLimit=180)))
    bg=alt.Chart(d).mark_bar(height=34,color='#263c46',cornerRadius=4).encode(x=alt.X('end:Q',title='30-day response histories within your contact cap (%)',scale=alt.Scale(domain=[0,100],nice=False),axis=alt.Axis(values=[0,25,50,75,100])),**enc)
    bars=alt.Chart(d).mark_bar(height=34,cornerRadius=4).encode(x='coverage:Q',color=alt.Color('profile:N',scale=SCALE,legend=None),**enc,tooltip=['profile',alt.Tooltip('coverage:Q',title='Within cap (%)',format='.1f'),alt.Tooltip('remainder:Q',title='Beyond cap (%)',format='.1f')])
    labels=alt.Chart(d).transform_filter(alt.datum.coverage>=18).mark_text(align='right',dx=-8,fontWeight=600,color='white',fontSize=14).encode(x='coverage:Q',text='label:N',**enc)
    short_labels=alt.Chart(d).transform_filter(alt.datum.coverage<18).mark_text(align='left',dx=8,fontWeight=600,color='#e0edeb',fontSize=14).encode(x='coverage:Q',text='label:N',**enc)
    return finish((bg+bars+labels+short_labels).properties(height=280))

def next_contact(frequency,cap):
    rows=[]
    for gid,a in frequency.groupby('segment_id'):
        c=np.interp([cap,cap+1],np.r_[0,a.contact_cap],np.r_[0,a.coverage])
        rows.append(dict(profile=GROUPS[gid],extra=100*(c[1]-c[0]),label=f'+{100*(c[1]-c[0]):.1f} pp'))
    d=pd.DataFrame(rows)
    bars=alt.Chart(d).mark_bar(height=24,cornerRadiusEnd=4).encode(x=alt.X('extra:Q',title=f'Extra response histories covered: cap {cap} → {cap+1} (percentage points)',scale=alt.Scale(domain=[0,38])),y=alt.Y('profile:N',sort=GROUPS,title=None,axis=alt.Axis(labelLimit=180)),color=alt.Color('profile:N',scale=SCALE,legend=None),tooltip=['profile',alt.Tooltip('extra:Q',title='Additional coverage (pp)',format='.1f')])
    text=alt.Chart(d).mark_text(align='left',dx=7,fontSize=13,color='#e0edeb').encode(x='extra:Q',y=alt.Y('profile:N',sort=GROUPS),text='label:N')
    return finish((bars+text).properties(height=280))

def response_opportunity(groups,shapes,day):
    d=groups.merge(shapes.query('day==@day')[['segment_id','response_share']],on='segment_id')
    d['speed']=100*d.response_share;d['potential']=10000*d.incremental_rate;d['share_pct']=100*d.share
    base=alt.Chart(d).encode(x=alt.X('speed:Q',title=f'Response captured by day {day} (%) →',scale=alt.Scale(domain=[0,105])),y=alt.Y('potential:Q',title='Benchmark extra conversions / 10,000 →',scale=alt.Scale(domain=[0,36])),color=alt.Color('profile:N',scale=SCALE,legend=None),tooltip=['profile',alt.Tooltip('speed:Q',title='Response captured (%)',format='.1f'),alt.Tooltip('potential:Q',title='Benchmark increment / 10k',format='.1f'),alt.Tooltip('share_pct:Q',title='Audience share (%)',format='.1f')])
    dots=base.mark_circle(opacity=.80,stroke='white',strokeWidth=2).encode(size=alt.Size('share_pct:Q',scale=alt.Scale(domain=[0,35],range=[0,2300]),legend=None))
    layers=[dots]
    for gid in range(5):
        layers.append(base.transform_filter(alt.datum.segment_id==gid).mark_text(dy=-28,fontSize=13,fontWeight=600).encode(text='profile:N'))
    return finish(alt.layer(*layers).properties(height=350))
