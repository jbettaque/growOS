from db.database import conn
from db.database_handler import get_all_runs
from model.hydro_run import HydroRun
from streamlit_local_storage import LocalStorage
import streamlit as st

def run_selector():
    local_storage = LocalStorage()
    runs = get_all_runs()
    if local_storage.getItem("selected_run_id") is None:
        selected_run = st.selectbox("Select run", runs)
        local_storage.setItem("selected_run_id", selected_run.id)
    else:
        selected_run_id = local_storage.getItem("selected_run_id")
        selected_run = None
        for run in runs:
            if run.id == selected_run_id:
                selected_run = run

        if (selected_run is not None):
            selected_run = st.selectbox("Select run", runs, index=runs.index(selected_run))
        else:
            selected_run = st.selectbox("Select run", runs)


        local_storage.setItem("selected_run_id", selected_run.id)
    return selected_run
