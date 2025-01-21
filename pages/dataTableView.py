import streamlit as st
import pandas as pd
from streamlit_local_storage import LocalStorage

from components.run_selector import run_selector
from db.database_handler import get_all_entries
from model.hydro_data_entry import HydroDataEntry, get_all_entries_df
from db.database import conn, init_db
from model.hydro_run import HydroRun

init_db()

st.set_page_config(layout="wide")

selected_run = run_selector()
all_entries = get_all_entries_df(get_all_entries())
st.write(all_entries)