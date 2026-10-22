"""Second visual: recorded advertising frequency and observed conversion labels."""
import json

import pandas as pd
import streamlit as st

from src.charts import frequency_chart
from src.frequency import FREQUENCY_ORDER, interval_table


@st.cache_data
def load_frequency(path,signature):
    return pd.read_parquet(path/'frequency.parquet'),json.loads((path/'frequency_run.json').read_text())


def render_frequency(path):
    if not (path/'frequency.parquet').exists():
        st.title('Advertising frequency')
        st.info('Prepare the attribution summary to view this chart.')
        st.code('.\\.venv\\Scripts\\python.exe scripts/prepare_frequency.py',language='powershell')
        return
    data,meta=load_frequency(path,tuple((path/name).stat().st_mtime_ns for name in
                                      ['frequency.parquet','frequency_run.json']))
    campaign_sizes=data.groupby('campaign').pairs.sum().sort_values(ascending=False)
    st.caption('THE INCREMENTALITY LAB / ADVERTISING FREQUENCY')
    st.header('How does repeat exposure relate to conversion?')
    st.write('Add campaign context to the segmentation discussion: compare response patterns '
             'with how often users appear in the advertising log.')
    with st.container(border=True):
        left,right=st.columns(2)
        with left:
            campaign=st.selectbox('Campaign',['All campaigns',*campaign_sizes.index],key='campaign',
                format_func=lambda x:x if x=='All campaigns' else f'Campaign {x} · {campaign_sizes[x]:,} pairs')
        with right:
            measure=st.radio('Frequency chart measure',['Conversion rate','Audience distribution'],
                             horizontal=True,key='frequency_measure')
        bins=st.multiselect('Frequency groups',FREQUENCY_ORDER,default=FREQUENCY_ORDER,key='frequency_bins')
    scope=data if campaign=='All campaigns' else data[data.campaign==campaign]
    aggregated=scope.groupby('frequency',as_index=False)[['pairs','converted_pairs','impressions']].sum()
    reference=aggregated.converted_pairs.sum()/aggregated.pairs.sum()
    selected=aggregated[aggregated.frequency.isin(bins)].copy()
    if selected.empty:
        st.warning('No frequency groups match these filters. Select at least one frequency group.')
        return
    selected=selected.assign(_order=selected.frequency.map({v:i for i,v in enumerate(FREQUENCY_ORDER)}))
    selected=selected.sort_values('_order').drop(columns='_order')
    selected=interval_table(selected)
    total=int(selected.pairs.sum())
    converted=int(selected.converted_pairs.sum())
    a,b,c=st.columns(3)
    a.metric('User–campaign pairs shown',f'{total:,}')
    b.metric('Pairs with a conversion label',f'{converted:,}')
    c.metric('Observed pair conversion rate',f'{converted/total:.2%}')
    with st.container(border=True):
        st.altair_chart(frequency_chart(selected,measure,reference,False),width='stretch',key='frequency_chart')
        st.caption('One observation = one user within one campaign. Frequency uses the entire released impression period. '
                   'Conversion = any impression in the pair has a conversion recorded within its following 30 days.')
        if measure=='Conversion rate':
            st.caption(f'Dashed line: all-frequency conversion rate in the selected campaign scope ({reference:.2%}). '
                       'Repeated positive impression labels are counted once per user–campaign pair.')
        st.caption('Observed association, not advertising lift. Customer intent and campaign mix can explain '
                   'the pattern; this chart does not establish a frequency cap or which campaign needs segmentation.')
