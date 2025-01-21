from streamlit_local_storage import LocalStorage

from db.database import conn
from model.hydro_data_entry import HydroDataEntry
from model.hydro_run import HydroRun


def get_all_entries():
    with (conn.session as session):
        local_storage = LocalStorage()
        username = local_storage.getItem("username")
        run_id = local_storage.getItem("selected_run_id")

        return session.query(HydroDataEntry).join(HydroRun).where(HydroDataEntry.run_id == run_id).where(HydroRun.username == username).order_by(HydroDataEntry.date.asc()).all()
        # return session.query(HydroDataEntry).where(HydroDataEntry.run_id == run_id).order_by(HydroDataEntry.date.asc()).all()

def get_all_runs():
    with conn.session as session:
        local_storage = LocalStorage()
        username = local_storage.getItem("username")
        runs = session.query(HydroRun).where(HydroRun.username == username).order_by(HydroRun.start_date.desc()).all()
        print(runs, username)
        return runs

def get_last_entry():
    with conn.session as session:
        local_storage = LocalStorage()
        username = local_storage.getItem("username")
        last_entry = session.query(HydroDataEntry).join(HydroRun).where(HydroRun.username == username).order_by(HydroDataEntry.date.desc(), HydroDataEntry.id.desc()).first()
        return last_entry