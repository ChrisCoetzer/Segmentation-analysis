"""Chat-style AI mockup: scripted, current-data explanations; no model calls."""
import streamlit as st
from src.investment import population_investment_scenario
from src.segmentation import cluster_average_comparison

QUESTIONS=[
    'Give me a summary of this chart.',
    'Why do conversions decrease at 32 groups?',
    'Is 32 groups worth more than 8 in this scenario?'
]


def choose_example(question):
    st.session_state['ai_question']=question


def submit_question():
    prompt=st.session_state.get('ai_prompt')
    if prompt:
        st.session_state['ai_question']=prompt


def render_ai_mock(groups,current,outcome_label,selected):
    with st.sidebar:
        st.header('AI assistant')
        st.caption('MOCKUP · scripted responses, no AI connected')
        st.markdown('**Try asking**')
        for i,question in enumerate(QUESTIONS):
            st.button(question,key=f'ai_suggestion_{i}',width='stretch',on_click=choose_example,args=(question,))
        question=st.session_state.get('ai_question',QUESTIONS[0])
        text=question.lower()
        st.caption(f'Chart context: {outcome_label.lower()} · {selected} groups selected')
        with st.container(height=440,border=True):
            with st.chat_message('user'):
                st.write(question)
            with st.chat_message('assistant'):
                if 'summary' in text or 'summarize' in text:
                    st.write('This chart explores whether finer customer segmentation helps identify audiences '
                             'that respond more to advertising. The model first clusters customers by feature '
                             'similarity, then uses separate data to select a responsive group at each level.')
                    st.write('The pattern suggests that finer groups can concentrate advertising response, '
                             'but those groups represent smaller portions of the customer base. A stronger average '
                             'response therefore does not necessarily mean more total conversions.')
                    st.write('Click a point on the graph to update the figures below it.')
                elif '32' in text and ('decrease' in text or 'dip' in text or 'conversion' in text):
                    conversion=cluster_average_comparison(groups,'conversion')
                    a=conversion[conversion.segments==16].iloc[0]
                    b=conversion[conversion.segments==32].iloc[0]
                    delta=(b['value']-a['value'])*10000
                    st.write(f'The conversion estimate changes from {a["value"]*10000:,.1f} at 16 groups '
                             f'to {b["value"]*10000:,.1f} at 32: a difference of {delta:+,.1f} per 10,000 cluster members.')
                    st.write('These clusters have no named customer labels or personas. They group users by '
                             'similarity in their anonymous features, without using conversion outcomes. '
                             'Splitting similar customers into finer groups does not guarantee more advertising gain.')
                    overlap=max(a['value']-1.96*a['se'],b['value']-1.96*b['se'])<=min(
                        a['value']+1.96*a['se'],b['value']+1.96*b['se'])
                    if delta>=0:
                        st.write('There is no dip in the current model run: the selected 32-group cluster '
                                 'has a higher measured conversion lift than the selected 16-group cluster.')
                    if overlap:
                        st.write('Look at the vertical uncertainty bars at 16 and 32: they overlap. '
                                 'The smaller 32-group cluster has fewer users; smaller samples generally '
                                 'make estimates less precise. The point estimates alone do not establish '
                                 'a reliable difference.')
                    else:
                        st.write('Compare the vertical uncertainty bars as well as the point estimates. '
                                 'Smaller clusters have fewer users and generally less precise estimates.')
                    st.caption('Source: conversion cluster averages · 16 and 32 groups')
                elif any(word in text for word in ['scenario','simulator','campaign','worth','advertis','population']):
                    population=st.session_state.get('investment_population',100000)
                    reach=st.session_state.get('investment_reach',12.5)
                    st.write(f'Your scenario selects {population*reach/100:,.0f} customers '
                             f'({reach:g}% of {population:,}) in every option.')
                    try:
                        data=population_investment_scenario(groups,population,reach,
                            st.session_state.get('investment_baseline',10.),
                            st.session_state.get('investment_contribution',100.))
                        a=data[data.segments==8].iloc[0]
                        b=data[data.segments==32].iloc[0]
                        st.write(rf'Break-even segmentation spend: \${a.break_even_cost:,.0f} for 8 groups '
                                 rf'and \${b.break_even_cost:,.0f} for 32 groups.')
                        st.write(rf'The difference is \${b.break_even_cost-a.break_even_cost:+,.0f} '
                                 'under your current assumptions. This is extra spending the modeled response '
                                 'could support, not guaranteed profit.')
                        st.caption(f'8 groups: {a.selection}. 32 groups: {b.selection}.')
                    except ValueError:
                        st.write('Adjust the scenario inputs to calculate a valid break-even amount.')
                    st.caption('Source: current population simulator · client assumptions')
                else:
                    st.write('This mockup demonstrates chart summaries, the 32-group conversion dip, '
                             'and campaign comparisons. Try one of the questions above; open-ended AI answers are planned.')
        st.chat_input('Ask about the charts…',key='ai_prompt',on_submit=submit_question)
        with st.expander('Planned AI role'):
            st.markdown('**Role:** Explain results, compare options, and suggest what to investigate next.\n\n'
                        '**Inputs:** Your question, current chart/filter selections, computed summaries, '
                        'uncertainty, and scenario assumptions.\n\n'
                        '**Outputs:** A short explanation with source-linked numbers and a suggested next check.\n\n'
                        '**Checks:** Recalculate numeric claims in Python, match source rows and filters, '
                        'and distinguish observations from scenario assumptions.')
