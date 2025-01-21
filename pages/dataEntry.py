from datetime import date
import streamlit as st
import pandas as pd
from model.hydro_data_entry import HydroDataEntry, conn
st.set_page_config(layout="centered")

def get_last_entry():
    with conn.session as session:
        last_entry = session.query(HydroDataEntry).order_by(HydroDataEntry.date.desc(), HydroDataEntry.id.desc()).first()
        return last_entry

def submit_data(data):
    today = date.today()

    try:
        if len(data) == 7:  # measure_only_mode
            # Create new measurement instance
            measurement = HydroDataEntry(
                date=today,
                ph_initial=float(data[0]),
                ec_initial=float(data[1]),
                ph_final=float(data[0]),  # Same as initial in measure only mode
                ec_final=float(data[1]),  # Same as initial in measure only mode
                light_hours=int(data[2]),
                light_intensity=int(data[3]),
                other_actions=str(data[4]),
                observations=str(data[5]),
                comments=str(data[6]),
                # These will use the default 0 values
                ph_down_added=0,
                ph_up_added=0,
                hydro_vega_added=0,
                hydro_flora_added=0,
                boost_added=0,
                water_temp=0,
                water_added=0,
                water_level=0,
                humidity=0,
                air_temp=0,
            )
        else:  # full mode
            measurement = HydroDataEntry(
                date=today,
                ph_initial=float(data[0]),
                ec_initial=float(data[1]),
                ph_final=float(data[2]),
                ec_final=float(data[3]),
                ph_down_added=float(data[4]),
                ph_up_added=float(data[5]),
                hydro_vega_added=float(data[6]),
                hydro_flora_added=float(data[7]),
                boost_added=float(data[8]),
                light_hours=int(data[9]),
                light_intensity=int(data[10]),
                other_actions=str(data[11]),
                observations=str(data[12]),
                comments=str(data[13])
            )

        # Save to database
        with conn.session as session:
            session.add(measurement)
            session.commit()

            # Show success message
            st.success('Entry has been added successfully to database', icon="✅")
            st.write(measurement.__df__())
            return

    except Exception as e:
        st.error(f'Error creating entry: {str(e)}')
        return None

measure_only_mode = st.toggle("Measure only mode", value=True)

with st.form(key='dataEntryForm'):
    if measure_only_mode:
        col1, col2 = st.columns(2)
        with col1:
            ph = st.number_input("pH")
        with col2:
            ec = st.number_input("EC")
    else:
        st.write("Initial Values before any actions")
        col1, col2 = st.columns(2)

        with col1:
            ph = st.number_input("pH")
        with col2:
            ec = st.number_input("EC")

        st.divider()
        st.write("Final Values after actions")
        col1, col2 = st.columns(2)

        with col1:
            ph_final = st.number_input("Final pH")
        with col2:
            ec_final = st.number_input("Final EC")

        st.divider()
        st.write("Added Substances")
        col1, col2 = st.columns(2)
        with col1:
            ph_down_added = st.number_input("pH- added (ml)", value=0)
            hydro_vega_added = st.number_input("hydro vega added (ml)", value=0)
            rhizotonic_added = st.number_input("rhizotonic added (ml)", value=0)
        with col2:
            ph_up_added = st.number_input("pH+ added (ml)", value=0)
            hydro_flora_added = st.number_input("hydro flora added (ml)", value=0)
            boost_added = st.number_input("boost added (ml)", value=0)

    st.divider()
    st.write("Light")

    last_entry = get_last_entry()

    last_entry_hours = last_entry.light_hours if last_entry else 12
    light_hours = st.number_input("light hours", value=last_entry_hours)

    last_light_intensity = last_entry.light_intensity if last_entry else 100
    light_intensity = st.number_input("light intensity %", value=last_light_intensity)

    st.divider()
    st.write("Human Comments")
    other_actions = st.text_area("Other Actions")
    observations = st.text_area("Observations")
    comments = st.text_area("Comments")

    submitted = st.form_submit_button("Enter Data")
    if submitted:

        if measure_only_mode:
            submit_data([ph, ec, light_hours, light_intensity, other_actions, observations, comments])
        else:
            submit_data([ph, ec, ph_final, ec_final, ph_down_added, ph_up_added, hydro_vega_added, hydro_flora_added, boost_added, light_hours, light_intensity, other_actions, observations, comments])
