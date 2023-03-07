import pandas as pd
import numpy as np
import datetime
import streamlit as st
import plotly.express as px
from PIL import Image

# Page Setting
st.set_page_config(layout="wide", page_title="MediaAlpha Takehome Exercise")

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

image = Image.open('images/logo.png')
st.image(image, width=200)

st.header("Takehome Exercise")
st.subheader("by Andres Hincapie")

st.markdown("_______________")

# Load Data
hlm = pd.read_csv('hlm.csv')
pc = pd.read_csv('pc.csv')

#### Data Cleaning and Transformation

# Clean-up date column for the hlm dataset. Transform 'date' column from '20/06/02' format -> '2020-06-02' format
hlm['year'] = hlm['date'].apply(lambda x: x[0:2])
hlm['month'] = hlm['date'].apply(lambda x: x[3:5])
hlm['day'] = hlm['date'].apply(lambda x: x[6:])
hlm['date'] = pd.to_datetime(hlm['month']+'-'+hlm['day']+'-'+hlm['year'])

hlm.drop(['day', 'month', 'year'], axis=1, inplace=True)

# Transform 'date' column in the pc dataset from string to date
pc['date'] = pd.to_datetime(pc['date'])

# Put together both datasets for analysis
full_df = pd.concat([hlm, pc], axis=0)

# Compute RPC
full_df['rpc'] = full_df['clicks_rev'] / full_df['clicks']


#### Question 1: Which 3 hour window across the entire date range shows the largest amount of clicks?

# Sum all clicks per date + time
clicks = full_df.groupby(['date', 'time'], as_index=False)['clicks'].sum()

# Sum total clicks over 3 hour rolling windows
# This column sums the number of clicks at each hour + the clicks in the next two hours (next two rows)
clicks['click_next_3_hours'] = clicks['clicks'] + clicks['clicks'].rolling(2).sum().shift(-2)

# List the end time and end date of the 3 hour window with the highest number of clicks
clicks['mid_time'] = clicks['time'].shift(-1)
clicks['max_time'] = clicks['time'].shift(-2)
clicks['max_date'] = clicks['date'].shift(-2)

# Transform time columns from string to time format
clicks['time'] = pd.to_datetime(clicks['time'],format= '%H:%M:%S' ).dt.time
clicks['max_time'] = pd.to_datetime(clicks['max_time'],format= '%H:%M:%S' ).dt.time

# Create a string of 3 hour time ranges to make it easier to display the 3 hour window with the highest number of clicks
clicks['time_range'] = clicks['time'].apply(lambda x: str(x.hour)) + ' - ' + clicks['max_time'].apply(lambda x: str(x.hour))

# Find the date and time range with the largest amount of clicks in a 3 hour window
max_clicks = clicks[clicks['click_next_3_hours'] == clicks['click_next_3_hours'].max()]

# Clean up the DataFrame and show the final results
max_clicks['clicks_next_3_hours'] = max_clicks['click_next_3_hours']
max_clicks.drop('click_next_3_hours', axis=1, inplace=True)

# Get date and time range with the largest amount of clicks in 3 hours
clicks_start_date = max_clicks['date'].dt.date.values[0]
clicks_end_date = max_clicks['max_date'].values[0] # In case the window falls between two different days, i.e. the time range include 12AM and 1 AM
clicks_start_time = str(max_clicks['time'].values[0])
clicks_mid_time = str(max_clicks['mid_time'].values[0])
clicks_end_time = str(max_clicks['max_time'].values[0])
clicks_time_range = max_clicks['time_range'].values[0]
clicks_in_three_hours = int(max_clicks['clicks_next_3_hours'].values[0])

clicks_result_str = " * The 3 hour window with the largest amount of clicks happens on **" \
                      + str(clicks_start_date) + " between "  + clicks_start_time + " and " + clicks_end_time \
                      + "**, with a total of **" + str(clicks_in_three_hours) + " clicks!**"

st.markdown("##### **Question 1**: Which 3 hour window across the entire date range shows the largest amount of clicks? :clock3:")
st.markdown(clicks_result_str)
st.markdown('\n')
st.markdown('\n')

#### Question 2: For the 3 hour window you found in question 1, what percent of the clicks in these 3 hours were “mobile”?

# Filter dataset to date and times with the highest number of clicks in a 3 hour window
full_date = full_df[full_df['date'] == pd.to_datetime(clicks_start_date)]
full_date = full_date[full_date['time'].isin([clicks_start_time, clicks_mid_time, clicks_end_time])]

# Sum clicks by device
by_device = full_date.groupby('device', as_index=False)['clicks'].sum()

# Calculate the percentage share of clicks per device and sort by descending percent share
by_device['percent'] = (by_device['clicks'] / by_device['clicks'].sum()) * 100
by_device = by_device.sort_values(by='percent', ascending=False)

mobile_pct_share = by_device[by_device['device'] == 'mobile']['percent'].values[0]
mobile_pct_share = str(round(mobile_pct_share)) + '%'

computer_pct_share = by_device[by_device['device'] == 'computer']['percent'].values[0]
computer_pct_share = str(round(computer_pct_share)) + '%'

tablet_pct_share = by_device[by_device['device'] == 'tablet']['percent'].values[0]
tablet_pct_share = str(round(tablet_pct_share)) + '%'

st.markdown("_______________")

st.markdown("##### **Question 2**: For the 3 hour window you found in question 1, what percent of the clicks in these 3 hours were “mobile”? :iphone:")
st.markdown("Click on the legend to remove specific devices from the chart!")

pie_chart = px.pie(by_device, title=" ", values='clicks', names='device')

pie_chart.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
},
    title = {
     'text': '<b>Click Distribution by Device</b>',
        'y': 0.9,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
})

st.plotly_chart(pie_chart, use_container_width=True)

# Streamlit Metrics Row A
a1, a2, a3= st.columns(3)
a1.metric("Mobile", mobile_pct_share)
a2.metric("Computer", computer_pct_share)
a3.metric("Tablet", tablet_pct_share)

st.markdown('\n')
st.markdown('\n')

#### Question 3: Graph the time series of clicks on datetime; x-axis should be datetime, y-axis should be clicks.

plot_df = full_df.copy()
plot_df['date'] = plot_df['date'].apply(lambda x: str(x.date()))
plot_df['timestamp'] = plot_df['date'] + ' ' + plot_df['time']
plot_df['timestamp'] = pd.to_datetime(plot_df['timestamp'])

date_list = plot_df['timestamp'].unique().tolist()

min_date = pd.to_datetime(min(date_list))
max_date = pd.to_datetime(max(date_list))

st.markdown("_______________")

st.markdown("##### **Question 3**: Graph the time series of clicks on datetime :chart_with_upwards_trend:")

# Create a slider for the line graph
# date_selection = st.slider('Date:', 
#                             min_value=min_date, 
#                             max_value=max_date, 
#                             value=(min_date, max_date)
#                             )

# mask = plot_df['timestamp'].between(*date_selection)

# line_df = plot_df[mask].groupby('timestamp', as_index=False)['clicks'].sum()
line_df = plot_df.groupby('timestamp')['clicks'].sum()

# Clicks Line Graph
fig_line = px.line(data_frame=line_df, y='clicks',
              labels = {
                  'timestamp': 'Date and Time',
                  'clicks': 'Number of Clicks'
               }
              )

fig_line.update_traces(line_color='#f84c24')

fig_line.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
},
    title = {
     'text': '<b>Total Clicks per Hour</b>',
        'y': 0.9,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
})

fig_line.update_xaxes(type='category')

# Click Distribution Bar Graph
group_line_df = plot_df.groupby(['product', 'device'], as_index=False)['clicks'].sum().sort_values(by='clicks')

fig_bar = px.histogram(data_frame=group_line_df, x='product', y='clicks', color='device', barnorm='percent', text_auto='.2f',
              labels = {
                  'product': 'Product',
                  'clicks': 'Clicks'
               }
              )

fig_bar.update_layout({
    'plot_bgcolor': 'rgba(0, 0, 0, 0)',
    'paper_bgcolor': 'rgba(0, 0, 0, 0)',
},
    title = {
     'text': '<b>Click Device Distribution by Product</b>',
        'y': 0.9,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'
},
)

# Show graphs on Streamlit Dash
st.plotly_chart(fig_line, use_container_width=True)

st.markdown("**Bonus Graph!** :tada: I also wanted to show the distribution of device clicks per product as an example of other things we can do with Streamlit.")
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown('\n')
st.markdown('\n')

#### Question 4: For each product, find the hour (time) that shows the highest RPC

# Create a list of the indices with the max RPC per hour (time) per product
max_rpc_hour = full_df.groupby(['product', 'time'], as_index=False).agg({'clicks': 'sum', 'clicks_rev':'sum'})
max_rpc_hour['rpc'] = max_rpc_hour['clicks_rev'] / max_rpc_hour['clicks']

max_rpc_hour_group = max_rpc_hour.groupby('product', as_index=False)['rpc'].idxmax()
index_list = list(max_rpc_hour_group['rpc'])

# Filter DataFrame to only show rows with the the highest RPC per product
max_hour_df = max_rpc_hour.iloc[index_list]
max_hour_df = max_hour_df.sort_values(by='rpc', ascending=False).reset_index()
max_hour_df.drop('index', axis=1, inplace=True)

st.markdown("_______________")

# Display in Streamlit
st.markdown("##### **Question 4**: For each product, find the hour (time) that shows the highest RPC :moneybag:")

st.table(max_hour_df)