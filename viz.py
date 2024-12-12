#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import altair as alt
from vega_datasets import data
import json


# ### Viz 1: History

# In[262]:


# events
df = pd.read_excel('history.xlsx')


# In[261]:


# map

comparison_colors=['orange','steelblue','green']
# 国家地理数据
countries_url = data.world_110m.url
world = alt.topo_feature(countries_url, 'countries')

base = alt.Chart(world, height=400, width=600).mark_geoshape(
    fill='lightgray',
    stroke='white'
).transform_filter(
    "datum.id!='010'"
).project(
    type='mercator'
)

events = alt.Chart(df).mark_point(stroke=None, fill='green', size=200).encode(
    longitude='lon:Q',
    latitude='lat:Q',
    fill=alt.Color('type:N', scale=alt.Scale(
        domain=['incandescent', 'cfl', 'led'],
        range=comparison_colors
    ), title='Type'),
    tooltip=['year:N','People:N','Achievement:N']
)

viz1 = alt.layer(base, events)
viz1.save('viz1.html')


# ### Viz 2: Comparison

# In[55]:


df = pd.read_excel('energy.xlsx')
df.head()


# In[56]:


# LED Energy saving
df_melted = df.melt(id_vars='type', var_name='source', value_name='value')


# In[113]:


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


# In[97]:


# selection
xscale = alt.selection_interval(bind='scales', encodings=['x'])
continent_dropdown = alt.binding_select(options=['North America', 'Seoul Semi & Samsung',  'Asia', 'Europe'], name='Region:')
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
viz3=(line_chart+vertical_line+dot+text_close+text_timestamp).configure_view(strokeWidth=0)
viz3.save('viz3.html')


# ### Streamlit

# In[264]:


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

st.markdown(""" In the beginning, humanity relied on the light of the sun to guide their days. People fear darkness and seek ways to gain light during the nights. The first artificial light was none other than fire — the primal discovery that sparked a revolution in human life. In the 18th century filled with innovation and upheaval, William Murdoch introduced gas lighting to the world, a miraculous leap forward. Imagine the bustling streets of 19th-century London suddenly lit by bright, steady gas lamps. These lights transformed cities, making nighttime activities safer and more common.

The real game changer came in the late 19th century when Thomas Edison and Joseph Swan independently developed the incandescent light bulb, which was pure magic at that time. As the 20th century dawned, stable, efficient fluorescent lighting brought a new era of brightness to offices and homes.""")

with open('viz1.html', 'r', encoding='utf-8') as f:
    html_content = f.read()
st.components.v1.html(html_content, height=500)

st.markdown(""" The crowning achievement of the artificial light saga might just be the invention of the LED. You can view the key nodes in the development of human electronic lighting on the map above. It is these great scientists who have created a colorful world for us. 

The earliest LEDs did not "glow", but emitted low-intensity infrared light, which was used to remotely control circuits. In 1962, Nick Holenyak of General Electric developed the first practical visible light emitting diode. Early LEDs were often used as indicator lights, replacing small incandescent bulbs. For a long time, people thought that LEDs could only be used as indicator light sources. They were far less bright than incandescent and fluorescent lamps, and most importantly, they could not emit white light.

In 1993, Shuji Nakamura, who worked at Nichia Corporation in Japan, successfully doped magnesium to create a blue light-emitting diode with commercial application value based on wide-bandgap semiconductor materials gallium nitride and indium gallium nitride (InGaN). White light-emitting diodes using yellow phosphors were also introduced. This also led to the Japanese engineer Hiroshi Amano, Isamu Akasaki and Shuji Nakamura winning the Nobel Prize in Physics in 2014 for "inventing high-brightness blue light-emitting diodes, which brought energy-saving and bright white light sources."
""")

st.image('nobel.jpg', caption='Nobel Prize in Physics (2014)', use_column_width=True)

st.markdown(""" In 2005, Cree, Inc. demonstrated a prototype white light emitting diode that achieved a record efficiency of 70 lm per watt at 350 mW. This allowed LED to officially enter the lighting market and begin to flourish. 

Today, our world is illuminated by lights of countless colors and intensities that are efficient, energy-efficient, and durable, lighting everything from micro devices to large stadiums.
""")

# paragraph 2
st.write("### Why choosing LED?")

st.markdown(""" There is no doubt that the LED market is growing year by year and is gradually replacing incandescent lamps and CFLs. So why are we choosing LED more and more? In fact, at today's technology, LED has shown its huge advantages in all aspects.
""")

st.image('icons.png', use_column_width=True)


st.markdown("""**Lifespan**: LEDs are significantly more durable, with an average lifespan of 25,000 to 50,000 hours, compared to incandescent bulbs that typically last only 1,000 hours and CFLs that last around 8,000 to 10,000 hours. This extended lifespan reduces the frequency of replacements and maintenance costs.

**Luminous Efficiency**: LEDs are far more energy-efficient, converting up to 90% of the energy they consume into light. Incandescent bulbs, on the other hand, waste most of their energy as heat, and CFLs, while more efficient than incandescent bulbs, still lag behind LEDs in this regard.

**Cost**: Although LEDs have a higher initial purchase cost, their energy savings and long lifespan make them the most cost-effective choice over time. Lower electricity bills and reduced replacement needs result in significant savings for both residential and commercial users.

**Heat Emission**: LEDs emit very little heat compared to incandescent bulbs, which release most of their energy as heat, making them inefficient and potentially hazardous. CFLs also produce more heat than LEDs, though less than incandescent bulbs. The lower heat output of LEDs makes them safer to use and reduces cooling costs in environments where heat management is a concern.
""")

with open('viz2.html', 'r', encoding='utf-8') as f:
    html_content = f.read()
st.components.v1.html(html_content, height=500)

st.markdown(""" The barplot above comes from a public report from Lamps Plus, which allows you to intuitively compare the advantages of LED lights.

LEDs have become an integral part of modern life, moving from being viewed as high-tech or niche products to being widely available and affordable solutions for a wide range of applications. Once considered a premium lighting option due to their advanced technology and initial cost, LEDs are now commonplace in homes, businesses, and public infrastructure. In everyday life, LEDs are used in everything from energy-efficient home lighting and decorative fixtures to televisions, computer screens, and smartphones. Their versatility also makes them an essential light source in automotive lighting, traffic lights, street lamps, and even wearable technology. Beyond lighting, LEDs power innovative applications such as smart home systems, horticultural lighting for indoor agriculture, and medical devices.
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.image("img1.jpg", caption="LED decoration", width=160)
with col2:
    st.image("img2.jpg", caption="Burton Memorial Tower in Ann Arbor", width=160)
with col3:
    st.image("img3.jpg", caption="LED spotlight", width=160)

st.markdown("""Turn on your smartphone or PC, or even the lighting in your refrigerator or microwave, and there’s a good chance it’s an LED product!
""")

# paragraph 3
st.write("### LED market")

st.markdown("""Today, the LED market remains a fascinating and rapidly evolving industry that has revolutionized the lighting industry. Its journey is intertwined with the pursuit of technological advancement, energy efficiency, and, increasingly, environmental protection.

The LED market is still full of opportunities and possibilities, accompanied by one peak after another. 
""")

with open('viz3.html', 'r', encoding='utf-8') as f:
    html_content = f.read()
st.components.v1.html(html_content, height=500)

st.markdown("""This line chart shows the historical stock prices of LED-related public companies in different regions (Samsung and Seoul Semiconductor are listed separately because they are particularly large.

We can find some interesting events from the chart. In 2000, Nakamura Shuji left the company due to a patent dispute with Nichia Chemical and provided consulting services to Cree (now Wolfspeed). Cree was the first company to successfully commercialize blue LEDs based on silicon carbide (SiC) substrates in the end of 1990s. This led to its rapid development in the early 21st century.

The next peak was in 2017-2018, during which the EU launched a plan to phase out halogen lamps, requiring member states to gradually reduce the use of traditional halogen lamps. The new regulations promoted the market demand for LED replacements. At the same time, the Chinese government completely banned the import and sale of incandescent lamps and encouraged the use of energy-efficient LED lighting equipment.

The recent peak was at the end of 2021, when countries launched large-scale economic stimulus plans after COVID-19, many of which were related to green energy and smart cities. These projects drove demand for LED lighting and display equipment. At the same time, companies such as Apple and Samsung gradually applied Mini LED technology to smartphones, laptops and other fields.
""")

# paragraph 4
st.write("### The Future")

st.markdown("""
The future of LED technology is full of possibilities. Beyond lighting, LEDs are becoming key in smart systems, sustainable energy solutions, and advanced applications like plant growth lights and wearable devices. With the rise of new technologies like quantum dots, micro-LEDs, and OLEDs, LEDs will become even more efficient, versatile, and environmentally friendly.

As LEDs continue to improve, they will help address global challenges like energy conservation and climate change while enhancing our daily lives. From homes to cities, LEDs light not only our world but also the path to a brighter, more sustainable future.""")


# In[ ]:




