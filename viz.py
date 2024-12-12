#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import altair as alt
from vega_datasets import data
import json


# ### Icon

# In[2]:


from PIL import Image
import matplotlib.pyplot as plt

image_path = "icons.png"
image = Image.open(image_path)

plt.imshow(image)
plt.axis('off')  
plt.show()


# ### Viz 1: History

# In[86]:


# events
df = pd.read_excel('history.xlsx')


# In[87]:


df['decade'] = (df['year']//10)*10
df['code'] = df['code'].astype(str)
df.head(30)


# In[93]:


# map
countries_url = data.world_110m.url
world = alt.topo_feature(countries_url, 'countries')

year_selection = alt.selection_point(
    name='Year', 
    fields=["year"], 
    bind=alt.binding_range(min=1800, max=2020, step=10),
    value=[{"year": 1800}]  # default year
)

# 动态高亮图层


base = alt.Chart(world).mark_geoshape(
    stroke='white'
).transform_filter(
    "datum.id != '010'"
).encode(
    # 默认地图填充颜色
    color=alt.condition(
        "datum.highlight==1",  # 使用动态字段高亮
        "type:N",
        alt.value("lightgray")
    )
).properties(
    width=800,
    height=400
)

highlight_layer = base.transform_lookup(
    lookup='id',
    from_=alt.LookupData(df, 'code', ['decade']),
).transform_calculate(
    highlight="datum.decade==Year.year?1:0"
).add_params(
    year_selection
)


# ### Viz 2: Comparison

# In[55]:


df = pd.read_excel('energy.xlsx')
df.head()


# In[56]:


# LED Energy saving
df_melted = df.melt(id_vars='type', var_name='source', value_name='value')


# In[57]:


comparison_colors=['#F6C6AD', '#A6CAEC', '#B4E5A2']
dropdown = alt.binding_select(options=df_melted['type'].unique().tolist(), name='Attribute ')
selector = alt.selection_point(fields=['type'], bind=dropdown, value=[{'type': 'Lifespan (h)'}])

viz2 = alt.Chart(df_melted, width=500, height=300).mark_bar(size=60).encode(
    x=alt.X('source:N', title=None, axis=alt.Axis(labelAngle=0), sort=['incandescent', 'cfl', 'led']),
    y=alt.Y('value:Q', title=None),
    color=alt.Color('source:N', scale=alt.Scale(
        domain=['incandescent', 'cfl', 'led'],
        range=comparison_colors
    ), title='Light')
).add_params(
    selector
).transform_filter(
    selector
)

viz2.save('viz2.html')


# ### Viz 3: Stock Price

# In[45]:


import yfinance as yf

# LED related companies list
clist = ['NICFF', '046890.KQ', '005930.KS', 'WOLF', '600703.SS', '002745.SZ', 'LIGHT.AS', '300323.SZ', 'LEDS', 'AYI', 'OSAGF']
cnames = [
    "Nichia Corporation",
    "Seoul Semiconductor Co., Ltd.",
    "Samsung Electronics Co., Ltd.",
    "Wolfspeed Inc. (formerly Cree Inc.)",
    "San'an Optoelectronics Co., Ltd.",
    "MLS Co., Ltd.",
    "Signify (formerly Philips Lighting)",
    "HC Semitek Corporation",
    "SemiLEDs Corporation",
    "Acuity Brands, Inc.",
    "OSRAM Licht AG"
]
ccontinent = ['Asia', 'Seoul Semi & Samsung', 'Seoul Semi & Samsung', 'North America', 'Asia', 'Asia', 'Europe', 'Asia', 'North America', 'North America', 'Europe']

# get stock price
def fetch_stock_data(i):
    stock_data = yf.Ticker(clist[i]).history(period="max")
    if not stock_data.empty:
        stock_data['code'] = clist[i]
        stock_data['corporation'] = cnames[i]
        stock_data['continent'] = ccontinent[i]
    return stock_data

all_stock_data = pd.concat([fetch_stock_data(i) for i in range(0, len(clist))]).reset_index()
all_stock_data['Close'] = abs(all_stock_data['Close'])
all_stock_data['Date'] = pd.to_datetime(all_stock_data['Date'], utc=True)

all_stock_data['YearMonth'] = all_stock_data['Date'].dt.to_period('M')

monthly_avg = all_stock_data.groupby(['YearMonth', 'code', 'corporation', 'continent']).mean().reset_index()
monthly_avg['YearMonth'] = monthly_avg['YearMonth'].astype(str)


# In[50]:


# selection
xscale = alt.selection_interval(bind='scales', encodings=['x'])
continent_dropdown = alt.binding_select(options=['North America', 'Seoul Semi & Samsung',  'Asia', 'Europe'], name='Continent:')
continent_selection = alt.selection_point(
    fields=['continent'],
    bind=continent_dropdown,
    name='Continent ',
    value=[{'continent': 'North America'}]
)
timestamp_selection = alt.selection_point(on='mousemove', encodings=['x'], nearest=True, empty='none')
timestamp_selection_opacity = alt.condition(timestamp_selection, alt.value(1), alt.value(0))

# line chart of stock price by time
line_chart = alt.Chart(monthly_avg).mark_line().encode(
    x=alt.X('YearMonth:T', title=None, scale=alt.Scale(domain=['2014-01-01', '2023-12-31']), axis=alt.Axis(format="%Y", labelAngle=0, tickCount='year')),
    y=alt.Y('Close:Q', title='Closing Price'),
    color=alt.Color('corporation:N', title='Corporation'),
    tooltip=['YearMonth:T', 'Close:Q', 'corporation:N']
).transform_filter(
    continent_selection
).add_params(
    xscale,
    continent_selection
).properties(
    width=550,
    height=300
)

vertical_line = alt.Chart(monthly_avg).mark_rule(color='lightgray', size=2).encode(
    x='YearMonth:T',
    opacity=timestamp_selection_opacity
).add_selection(
    timestamp_selection
)

dot = alt.Chart(monthly_avg).mark_point(size=50, opacity=0, fill='white').encode(
    x='YearMonth:T',
    y='Close:Q',
    color='corporation:N', 
    opacity=timestamp_selection_opacity
).transform_filter(
    continent_selection
)

text_close = alt.Chart(monthly_avg).mark_text(fontSize=12, align='left', dx=7).encode(
    x='YearMonth:T',
    y='Close:Q',
    color='corporation:N',
    text=alt.condition(timestamp_selection, alt.Text('Close:Q', format=".2f"), alt.value('')),
    opacity=timestamp_selection_opacity
).transform_filter(
    continent_selection
)

text_timestamp = alt.Chart(monthly_avg).mark_text(fontSize=12, align='left', dx=7, dy=-130, color='lightgray').encode(
    x='YearMonth:T',
    text=alt.condition(timestamp_selection, alt.Text('YearMonth:T', format='%b %Y'), alt.value(''))
).transform_filter(
    continent_selection
)

# save chart
viz4=(line_chart+vertical_line+dot+text_close+text_timestamp).configure_view(strokeWidth=0)
viz4.save('viz4.html')


# ### Viz 4 Global Development

# ### Streamlit

# In[12]:


import streamlit as st

# title
st.title("The Evolution of LED")
st.markdown(
    """
    <style>
    .custom-text {
        font-size: 16px; /* fontsize */
        color: gray;     /* fontcolor */
    }
    </style>
    <p class="custom-text"> Welcome to my blog! This is the narrative visualization project by Jiaxing Xu in SI 649 2024 Fall in University of Michigan. The interactive charts and text are built with Altair and Streamlit.</p>
    """,
    unsafe_allow_html=True
)

# paragraph 1
st.write("### Creating Light")
st.markdown(""" In the beginning, humanity relied on the light of the sun to guide their days. People fear darkness and seek ways to gain light during the nights. The first artificial light was none other than fire — the primal discovery that sparked a revolution in human life. In the 18th century filled with innovation and upheaval, William Murdoch introduced gas lighting to the world, a miraculous leap forward. Imagine the bustling streets of 19th-century London suddenly lit by bright, steady gas lamps. These lights transformed cities, making nighttime activities safer and more common.

The real game changer came in the late 19th century when Thomas Edison and Joseph Swan independently developed the incandescent light bulb, which was pure magic at that time. As the 20th century dawned, stable, efficient fluorescent lighting brought a new era of brightness to offices and homes.

The crowning achievement of the artificial light saga might just be the invention of the LED, energy-efficient, durable, and versatile, lighting up everything from tiny devices to massive stadiums. The earliest LEDs did not "glow", but emitted low-intensity infrared light, which was used to remotely control circuits. In 1962, Nick Holenyak of General Electric developed the first practical visible light emitting diode. Early LEDs were often used as indicator lights, replacing small incandescent bulbs.
""")

st.image("icons.png", caption="Three main types of electric light sources", width=300)

col1, col2, col3 = st.columns(3)
with col1:
    st.image("img1.jpg", caption="LED decoration", width=150)
with col2:
    st.image("img2.jpg", caption="Burton Memorial Tower", width=150)
with col3:
    st.image("img3.jpg", caption="LED spotlight", width=150)


# paragraph 2
st.write("### Development of LED")

# paragraph 2
st.write("### Why choosing LED?")
with open('viz2.html', 'r', encoding='utf-8') as f:
    html_content = f.read()
st.components.v1.html(html_content, height=500)

# paragraph 3
st.write("### LED market")
with open('viz4.html', 'r', encoding='utf-8') as f:
    html_content = f.read()
st.components.v1.html(html_content, height=500)

# paragraph 4
st.write("### The Future")


# In[ ]:




