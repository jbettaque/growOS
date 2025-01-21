import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from streamlit_local_storage import LocalStorage

from components.run_selector import run_selector
from db.database_handler import get_all_entries
from model.hydro_run import HydroRun
from pages.dataEntry import selected_run

st.set_page_config(layout="wide")

import pandas as pd
from datetime import datetime
import plotly.express as px



def plot_ph_chart(df):
    fig = go.Figure()

    # Add initial and final pH lines
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ph_initial'],
        name='Initial pH',
        line=dict(color='blue')
    ))

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ph_final'],
        name='Final pH',
        line=dict(color='red')
    ))

    # Create combined timeline
    combined_dates = []
    combined_ph = []
    for _, row in df.iterrows():
        combined_dates.extend([row['date'], row['date']])
        combined_ph.extend([row['ph_initial'], row['ph_final']])

    fig.add_trace(go.Scatter(
        x=combined_dates,
        y=combined_ph,
        name='Daily Progress',
        line=dict(color='gray', dash='dot')
    ))

    # Add optimal range
    fig.add_hrect(
        y0=5.2, y1=6.4,
        fillcolor="green", opacity=0.1,
        layer="below", line_width=0,
        name="Optimal Range"
    )

    fig.update_layout(
        title='pH Levels Over Time',
        xaxis_title='Date',
        yaxis_title='pH Level',
        hovermode='x unified'
    )

    return fig


def plot_ec_chart(df):
    fig = go.Figure()

    # Add initial and final EC lines
    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ec_initial'],
        name='Initial EC',
        line=dict(color='blue')
    ))

    fig.add_trace(go.Scatter(
        x=df['date'],
        y=df['ec_final'],
        name='Final EC',
        line=dict(color='red')
    ))

    # Create combined timeline
    combined_dates = []
    combined_ec = []
    for _, row in df.iterrows():
        combined_dates.extend([row['date'], row['date']])
        combined_ec.extend([row['ec_initial'], row['ec_final']])

    fig.add_trace(go.Scatter(
        x=combined_dates,
        y=combined_ec,
        name='Daily Progress',
        line=dict(color='gray', dash='dot')
    ))

    # Add optimal ranges
    fig.add_hrect(
        y0=0.9, y1=1.7,
        fillcolor="green", opacity=0.1,
        layer="below", line_width=0,
        name="Seedling Stage Range"
    )

    fig.add_hrect(
        y0=1.7, y1=1.9,
        fillcolor="green", opacity=0.2,
        layer="below", line_width=0,
        name="Mid Veg Stage Range"
    )

    fig.add_hrect(
        y0=1.9, y1=2.2,
        fillcolor="green", opacity=0.3,
        layer="below", line_width=0,
        name="Late Veg Stage Range"
    )

    fig.add_hrect(
        y0=2.2, y1=2.4,
        fillcolor="yellow", opacity=0.1,
        layer="below", line_width=0,
        name="Early Bloom Stage Range"
    )

    fig.add_hrect(
        y0=2.4, y1=2.6,
        fillcolor="yellow", opacity=0.2,
        layer="below", line_width=0,
        name="Bloom Stage Range"
    )

    fig.update_layout(
        title='EC Levels Over Time',
        xaxis_title='Date',
        yaxis_title='EC Level',
        hovermode='x unified'
    )

    return fig


def plot_substances_added(df):
    substances = ['ph_down_added', 'ph_up_added', 'hydro_vega_added',
                  'hydro_flora_added', 'boost_added', 'rhizotonic_added']

    fig = go.Figure()

    for substance in substances:
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df[substance],
            name=substance.replace('_', ' ').title()
        ))

    fig.update_layout(
        title='Substances Added Over Time',
        xaxis_title='Date',
        yaxis_title='Amount Added (ml)',
        barmode='group',
        hovermode='x unified'
    )

    return fig


def plot_light_metrics(df):
    """
    Creates a plot showing light hours as an area chart and light intensity as a line
    over time. Missing values are forward-filled with the last known value.

    Parameters:
        df (pandas.DataFrame): DataFrame with columns 'date', 'light_hours', and 'light_intensity'

    Returns:
        plotly.graph_objects.Figure: The configured plot
    """
    # Create a copy of the dataframe and forward fill missing values
    df_filled = df.copy()
    df_filled['light_hours'] = df_filled['light_hours'].ffill()
    df_filled['light_intensity'] = df_filled['light_intensity'].ffill()

    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add light hours as area
    fig.add_trace(
        go.Scatter(
            x=df_filled['date'],
            y=df_filled['light_hours'],
            name='Light Hours',
            fill='tozeroy',  # Creates the area effect
            line=dict(color='rgba(255, 223, 0, 0.8)'),  # More yellow, slightly transparent
            fillcolor='rgba(255, 223, 0, 0.3)',  # Light yellow, very transparent
            mode='lines'  # Ensures we're drawing lines
        ),
        secondary_y=False
    )

    # Add light intensity as line
    fig.add_trace(
        go.Scatter(
            x=df_filled['date'],
            y=df_filled['light_intensity'],
            name='Light Intensity',
            line=dict(color='orange', width=2),
            mode='lines'  # Ensures we're drawing lines
        ),
        secondary_y=True
    )

    # Update layout with better styling
    fig.update_layout(
        title={
            'text': 'Light Hours and Intensity Over Time',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        hovermode='x unified',
        showlegend=True,

        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
        ),
        margin=dict(l=60, r=60, t=50, b=50)  # Adjusted margins
    )

    # Update primary y-axis (Light Hours)
    fig.update_yaxes(
        title_text="Light Hours",
        secondary_y=False,
        gridcolor='rgba(0,0,0,0.1)',  # Light grid
        range=[0, max(df_filled['light_hours']) * 1.1],  # Add 10% padding to max
        zeroline=True,
        zerolinecolor='rgba(0,0,0,0.2)',
        zerolinewidth=1
    )

    # Update secondary y-axis (Light Intensity)
    fig.update_yaxes(
        title_text="Light Intensity",
        secondary_y=True,
        gridcolor='rgba(0,0,0,0.1)',  # Light grid
        zeroline=True,
        zerolinecolor='rgba(0,0,0,0.2)',
        zerolinewidth=1,
        range=[0, max(df_filled['light_intensity']) * 1.1]  # Add 10% padding to max
    )

    # Update x-axis
    fig.update_xaxes(
        gridcolor='rgba(0,0,0,0.1)',  # Light grid
        zeroline=False,
        showline=True,
        linewidth=1,
        linecolor='rgba(0,0,0,0.2)'
    )

    return fig


def plot_water_metrics(df):
    # Create three subplots for water metrics
    fig = make_subplots(
        rows=3, cols=1,
        subplot_titles=('Water Temperature', 'Water Level', 'Water Added')
    )

    # Water Temperature
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['water_temp'], name='Temperature (°C)',
                   line=dict(color='red')),
        row=1, col=1
    )

    # Water Level
    fig.add_trace(
        go.Scatter(x=df['date'], y=df['water_level'], name='Level (cm)',
                   line=dict(color='blue')),
        row=2, col=1
    )

    # Water Added
    fig.add_trace(
        go.Bar(x=df['date'], y=df['water_added'], name='Added (L)',
               marker_color='lightblue'),
        row=3, col=1
    )

    fig.update_layout(
        height=800,
        title_text="Water Metrics Over Time",
        showlegend=True
    )

    return fig


def plot_environment_metrics(df):
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add humidity line
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['humidity'],
            name='Humidity (%)',
            line=dict(color='blue')
        ),
        secondary_y=False
    )

    # Add temperature line
    fig.add_trace(
        go.Scatter(
            x=df['date'],
            y=df['air_temp'],
            name='Temperature (°C)',
            line=dict(color='red')
        ),
        secondary_y=True
    )

    fig.update_layout(
        title='Environmental Conditions Over Time',
        hovermode='x unified'
    )

    fig.update_yaxes(title_text="Humidity (%)", secondary_y=False)
    fig.update_yaxes(title_text="Temperature (°C)", secondary_y=True)

    return fig


def display_charts(df):
    """Main function to display all charts"""
    st.title('Hydroponic System Analytics')

    # EC Chart
    st.subheader('EC Levels')
    st.plotly_chart(plot_ec_chart(df), use_container_width=True)

    # pH Chart
    st.subheader('pH Levels')
    st.plotly_chart(plot_ph_chart(df), use_container_width=True)

    # Substances Added
    st.subheader('Nutrients and Additives')
    st.plotly_chart(plot_substances_added(df), use_container_width=True)

    # Light Metrics
    st.subheader('Light Metrics')
    st.plotly_chart(plot_light_metrics(df), use_container_width=True)

    # Water Metrics
    st.subheader('Water Metrics')
    st.plotly_chart(plot_water_metrics(df), use_container_width=True)

    # Environment Metrics
    st.subheader('Environmental Conditions')
    st.plotly_chart(plot_environment_metrics(df), use_container_width=True)


if __name__ == "__main__":
    # Assuming you have your data loading logic here
    from model.hydro_data_entry import get_all_entries_df, HydroDataEntry
    from db.database import init_db

    init_db()
    selected_run = run_selector()

    all_entries = get_all_entries_df(get_all_entries())
    display_charts(all_entries)