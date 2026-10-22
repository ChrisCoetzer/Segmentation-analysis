"""Altair charts built from small, precomputed evaluation tables."""
import altair as alt

TEAL = '#087F8C'
INK = '#18313F'


def depth_chart(data, title, selected, broad, show_intervals=False,story=False,interactive=False):
    base = alt.Chart(data).encode(
        x=(alt.X('audience_label:N',title='Increasingly detailed segmentation',
                  sort=['Broad audience','Responsive half','Responsive quarter','Responsive eighth','Responsive sixteenth'],
                  axis=alt.Axis(labelAngle=0)) if story else
           alt.X('segments:O', title='Number of customer segments', sort='ascending', axis=alt.Axis(labelAngle=0))),
        tooltip=[alt.Tooltip('segments:O',title='Segments'),
                 alt.Tooltip('reach:Q',title='Selected cluster share (%)',format='.1f'),
                 alt.Tooltip('estimate:Q',title='Estimated outcomes / 10,000',format='.2f'),
                 alt.Tooltip('lower:Q',title='Interval lower',format='.2f'),
                 alt.Tooltip('upper:Q',title='Interval upper',format='.2f')])
    line = base.mark_line(color=TEAL,strokeWidth=3).encode(y=alt.Y('estimate:Q',title=title,scale=alt.Scale(zero=True)))
    if interactive:
        pick=alt.selection_point(name='segment_pick',fields=['segments'],on='click',nearest=True,
                                 clear=False,toggle=False,value=[{'segments':selected}])
        dots=base.mark_circle(cursor='pointer').add_params(pick).encode(y='estimate:Q',
            size=alt.condition(pick,alt.value(170),alt.value(75)),
            color=alt.condition(pick,alt.value(INK),alt.value(TEAL)))
    else:
        dots=base.mark_circle().encode(y='estimate:Q',
            size=alt.condition(alt.datum.segments==selected,alt.value(170),alt.value(75)),
            color=alt.condition(alt.datum.segments==selected,alt.value(INK),alt.value(TEAL)))
    ref = alt.Chart().mark_rule(color='#859799',strokeDash=[5,5]).encode(y=alt.datum(broad))
    layers = [line, dots, ref]
    if show_intervals:
        layers.insert(0,base.mark_rule(color=TEAL,strokeWidth=2).encode(y='lower:Q',y2='upper:Q'))
    return alt.layer(*layers).properties(height=345).configure_axis(
        gridColor='#E0E7E5',labelFontSize=12,titleFontSize=12).configure_view(stroke=None)


def group_chart(data, outcome, show_intervals=False):
    base = alt.Chart(data).encode(
        y=alt.Y('group:O',title='Group (low to high estimated response)',sort='ascending'),
        tooltip=[alt.Tooltip('group:O',title='Group'),alt.Tooltip('share:Q',title='Audience share',format='.1%'),
                 alt.Tooltip('estimate:Q',title=f'Incremental {outcome} / 10,000',format='.2f'),
                 alt.Tooltip('lower:Q',title='Interval lower',format='.2f'),
                 alt.Tooltip('upper:Q',title='Interval upper',format='.2f'),
                 alt.Tooltip('treated:Q',title='Treated users',format=','),
                 alt.Tooltip('control:Q',title='Control users',format=',')])
    dots = base.mark_circle(color=TEAL,size=95).encode(
        x=alt.X('estimate:Q',title=f'Incremental {outcome} per 10,000 group members',scale=alt.Scale(zero=True)))
    zero=alt.Chart().mark_rule(color='#9BA9A8',strokeDash=[3,3]).encode(x=alt.datum(0))
    layers=[dots,zero]
    if show_intervals:
        layers.insert(0,base.mark_rule(color=TEAL,strokeWidth=2).encode(x='lower:Q',x2='upper:Q'))
    return alt.layer(*layers).properties(height=max(200,len(data)*42)).configure_view(stroke=None)


def frequency_chart(data, measure, reference, show_intervals=False):
    from src.frequency import FREQUENCY_ORDER
    is_rate=measure=='Conversion rate'
    base=alt.Chart(data).encode(
        x=alt.X('frequency:O',sort=FREQUENCY_ORDER,title='Recorded impressions per user within a campaign',
                axis=alt.Axis(labelAngle=0)),
        tooltip=[alt.Tooltip('frequency:O',title='Impressions'),
                 alt.Tooltip('pairs:Q',title='Userâ€“campaign pairs',format=','),
                 alt.Tooltip('converted_pairs:Q',title='Pairs with a conversion label',format=','),
                 alt.Tooltip('rate:Q',title='Conversion rate',format='.2%'),
                 alt.Tooltip('share:Q',title='Share of selected audience',format='.1%'),
                 alt.Tooltip('impressions:Q',title='Recorded impressions',format=',')])
    bars=base.mark_bar(cornerRadiusTopLeft=4,cornerRadiusTopRight=4,size=85,color=TEAL).encode(
        y=alt.Y('rate:Q' if is_rate else 'pairs:Q',
                title='Pairs with any conversion label (%)' if is_rate else 'Userâ€“campaign pairs',
                axis=alt.Axis(format='.1%' if is_rate else '~s'),scale=alt.Scale(zero=True)))
    layers=[bars]
    if is_rate:
        layers.append(alt.Chart().mark_rule(color=INK,strokeDash=[5,5]).encode(y=alt.datum(reference)))
        if show_intervals:
            layers.append(base.mark_rule(color=INK,strokeWidth=2).encode(y='lower:Q',y2='upper:Q'))
    return alt.layer(*layers).properties(height=355).configure_view(stroke=None).configure_axis(
        gridColor='#E0E7E5',labelFontSize=12,titleFontSize=12)
