import streamlit as st
import pandas as pd
from model.hydro_data_entry import HydroDataEntry, conn, get_all_entries_df

st.set_page_config(layout="wide")

def get_all_entries():
    with conn.session as session:
        return session.query(HydroDataEntry).order_by(HydroDataEntry.date.asc()).all()

all_entries = get_all_entries_df(get_all_entries())
st.write(all_entries)