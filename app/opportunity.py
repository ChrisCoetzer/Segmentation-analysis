"""Phase 2 opportunity: a transparent segmentation investment scenario."""
import altair as alt
import streamlit as st

from src.investment import population_investment_scenario


def render_opportunity(groups):
    st.caption('PHASE 2 / SEGMENTATION INVESTMENT SCENARIO')
    st.header('What could better segmentation be worth to you?')
    st.write('How much could you spend on segmentation before its extra conversion value is used up?')
    st.markdown('Choose a share of your customer population. Each model fills the same audience from its highest-ranked clusters.')
    with st.container(border=True):
        left,middle,right=st.columns(3)
        with left:
            population=st.number_input('Total customer population',min_value=0,max_value=1_000_000_000,
                                     value=100_000,step=1000,key='investment_population')
            reach=st.slider('Percentage to advertise to',0.,100.,12.5,.5,format='%.1f%%',key='investment_reach')
            targeted=population*reach/100
            st.metric('Customers selected',f'{targeted:,.0f}')
        with middle:
            baseline=st.number_input('Your baseline lift (conversions / 10,000)',min_value=0.,max_value=10000.,
                                     value=10.,step=1.,key='investment_baseline')
            st.caption('Extra conversions caused by advertising per 10,000 selected customers.')
        with right:
            contribution=st.number_input('Contribution per extra conversion ($)',min_value=0.,max_value=1_000_000.,
                                         value=100.,step=10.,key='investment_contribution')
            st.caption('Value remaining after variable business costs.')
    st.caption('The main chart inspects one cluster; this scenario combines clusters to fill the chosen audience. Dollar amounts are illustrative.')
    try:
        data=population_investment_scenario(groups,population,reach,baseline,contribution)
    except ValueError as error:
        st.warning(str(error))
        return
    options=data[data.segments>1].copy()
    st.subheader('How much segmentation spend could the added response support?')
    rows=list(options.itertuples())
    for start in range(0,len(rows),3):
        for column,row in zip(st.columns(3),rows[start:start+3]):
            column.metric(f'{row.segments} groups · break-even spend',f'${row.break_even_cost:,.0f}')
            column.caption(f'{row.additional_conversions:,.1f} extra conversions · {row.selection}.')
    with st.container(border=True):
        chart=alt.Chart(options).mark_bar(cornerRadiusEnd=4,color='#087F8C').encode(
            y=alt.Y('option:N',sort=options.option.tolist(),title=None),
            x=alt.X('break_even_cost:Q',title='Break-even segmentation spend for one campaign ($)',
                    axis=alt.Axis(format='$,.0f',tickCount=5),scale=alt.Scale(zero=True)),
            tooltip=[alt.Tooltip('option:N',title='Segmentation'),
                     alt.Tooltip('selection:N',title='Audience assembled from'),
                     alt.Tooltip('targeted_users:Q',title='Customers selected',format=',.0f'),
                     alt.Tooltip('additional_conversions:Q',title='Additional conversions (scenario)',format=',.1f'),
                     alt.Tooltip('break_even_cost:Q',title='Break-even segmentation spend',format='$,.0f')])
        st.altair_chart(chart.properties(height=max(215,len(options)*42)).configure_view(stroke=None),
                        width='stretch',key='investment_chart')
        st.write('Break-even spend is the total segmentation budget supported by the estimated extra '
                 'conversions, compared with random selection.')
        st.caption('Each amount is relative to broad targeting, not the additional budget for moving between group counts.')
        values=options.set_index('segments').break_even_cost
        counts=values.index.tolist()
        changes=[(left,right,values[right]-values[left]) for left,right in zip(counts,counts[1:])]
        st.write('Added break-even value at each doubling: '+ '; '.join(
            rf'{left} → {right}: \${change:,.0f}' for left,right,change in changes)+'.')
        if len(changes)>1 and targeted>0 and baseline>0 and contribution>0:
            latest=changes[-1]
            if latest[2]<0:
                st.caption(f'{latest[1]} groups performs worse than {latest[0]} at the selected audience percentage.')
            elif latest[2]<changes[-2][2]:
                st.caption('The latest doubling adds less value at the selected audience percentage.')
            else:
                st.caption('The latest doubling does not show a further slowdown at the selected audience percentage.')
        if targeted==0 or baseline==0 or contribution==0:
            st.info('These inputs produce no additional contribution to fund segmentation.')
