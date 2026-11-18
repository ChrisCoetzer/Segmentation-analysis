"""Visualize the real fitted decision rules and observed group sizes."""
import altair as alt
import pandas as pd


def tree_chart(structure,groups):
    nodes={r['node']:r for r in structure['nodes']}
    leaves={int(r.node):r for _,r in groups.iterrows()}
    positions={}
    next_x=[0]

    def visit(node,depth):
        row=nodes[node]
        if row['left']<0:
            x=next_x[0]
            next_x[0]+=1
        else:
            x=(visit(row['left'],depth+1)+visit(row['right'],depth+1))/2
        positions[node]=(x,-depth)
        return x

    visit(0,0)
    dots,edges=[] ,[]
    for node,row in nodes.items():
        x,y=positions[node]
        leaf=row['left']<0
        if leaf:
            g=leaves[node]
            label=f'Group {int(g.group)}\n{g.share:.1%} of users'
            description=f'{int(g.n):,} evaluation users; incremental effect: {g.effect*10000:.2f} per 10,000'
        else:
            label=f'{row["feature"]} ≤ {row["threshold"]:.6f}?'
            description=f'{row["feature"]} threshold {row["threshold"]:.12g}; left = yes, right = no'
            for child,answer in [(row['left'],'Yes'),(row['right'],'No')]:
                cx,cy=positions[child]
                edges.append(dict(x=x,y=y-.2,x2=cx,y2=cy+.2,label=answer,
                                  mx=(x+cx)/2,my=(y+cy)/2))
        dots.append(dict(x=x,y=y,x0=x-.44,x1=x+.44,y0=y-.21,y1=y+.21,
                         label=label,description=description,kind='Group' if leaf else 'Split'))
    node_frame=pd.DataFrame(dots)
    base=alt.Chart(node_frame)
    rect=base.mark_rect(cornerRadius=6).encode(
        x=alt.X('x0:Q',axis=None),x2='x1:Q',y=alt.Y('y0:Q',axis=None),y2='y1:Q',
        color=alt.Color('kind:N',scale=alt.Scale(domain=['Split','Group'],range=['#E0E9E8','#087F8C']),legend=None),
        tooltip=['label:N','description:N'])
    text=base.mark_text(lineBreak='\n',lineHeight=16,fontSize=12).encode(
        x=alt.X('x:Q',axis=None),y=alt.Y('y:Q',axis=None),text='label:N',
        color=alt.condition(alt.datum.kind=='Group',alt.value('white'),alt.value('#18313F')))
    layers=[]
    if edges:
        edge=alt.Chart(pd.DataFrame(edges))
        layers=[edge.mark_rule(color='#899D9D').encode(x=alt.X('x:Q',axis=None),
                    y=alt.Y('y:Q',axis=None),x2='x2:Q',y2='y2:Q'),
                edge.mark_text(fontSize=11,color='#536B6B',dy=-3).encode(
                    x=alt.X('mx:Q',axis=None),y=alt.Y('my:Q',axis=None),text='label:N')]
    return alt.layer(*layers,rect,text).properties(height=max(180,110*len(set(y for x,y in positions.values())))).configure_view(stroke=None)


def size_chart(data):
    return alt.Chart(data).mark_bar(color='#087F8C',cornerRadiusEnd=3).encode(
        y=alt.Y('group:O',title='Group'),
        x=alt.X('share:Q',title='Share of evaluation users',axis=alt.Axis(format='.0%'),scale=alt.Scale(domain=[0,1])),
        tooltip=[alt.Tooltip('group:O',title='Group'),alt.Tooltip('share:Q',title='Audience share',format='.1%'),
                 alt.Tooltip('n:Q',title='Users',format=',')]).properties(height=max(200,len(data)*42)).configure_view(stroke=None)
