from streamlit_local_storage import LocalStorage
import pandas as pd
import streamlit as st
from sqlalchemy.orm import joinedload

from db.database import get_db_session
from model.hydro_data_entry import HydroDataEntry, get_entry_from_df
from model.hydro_run import HydroRun


def get_entries_for_run(run_id, start_date=None, end_date=None):
    """Get entries for a specific run, optionally filtered by date range"""
    with get_db_session() as session:
        query = (session.query(HydroDataEntry)
                 .options(joinedload(HydroDataEntry.run))
                 .where(HydroDataEntry.run_id == run_id)
                 .order_by(HydroDataEntry.date.asc()))

        if start_date:
            query = query.where(HydroDataEntry.date >= start_date)
        if end_date:
            query = query.where(HydroDataEntry.date <= end_date)

        entries = query.all()
        session.expunge_all()
        return entries


def get_all_entries():
    """Get all entries for the current user and selected run"""
    with get_db_session() as session:
        local_storage = LocalStorage()
        username = local_storage.getItem("username")
        run_id = local_storage.getItem("selected_run_id")

        # Use joinedload to eagerly load relationships
        entries = (session.query(HydroDataEntry)
                   .options(joinedload(HydroDataEntry.run))
                   .join(HydroRun)
                   .where(HydroDataEntry.run_id == run_id)
                   .where(HydroRun.username == username)
                   .order_by(HydroDataEntry.date.asc())
                   .all())

        # Detach the objects from the session but ensure all necessary data is loaded
        session.expunge_all()
        return entries


def get_all_runs():
    """Get all runs for the current user"""
    with get_db_session() as session:
        local_storage = LocalStorage()
        username = local_storage.getItem("username")

        # Query runs and detach them from session
        runs = (session.query(HydroRun)
                .options(joinedload(HydroRun.entries))
                .where(HydroRun.username == username)
                .order_by(HydroRun.start_date.desc())
                .all())

        # Detach objects from session
        session.expunge_all()
        print(runs, username)
        return runs


def get_last_entry():
    """Get the last entry for the current user"""
    with get_db_session() as session:
        local_storage = LocalStorage()
        username = local_storage.getItem("username")

        last_entry = (session.query(HydroDataEntry)
                      .options(joinedload(HydroDataEntry.run))
                      .join(HydroRun)
                      .where(HydroRun.username == username)
                      .order_by(HydroDataEntry.date.desc(), HydroDataEntry.id.desc())
                      .first())

        if last_entry:
            session.expunge(last_entry)
        return last_entry


def get_entry_by_id(entry_id):
    """Get a specific entry by ID"""
    with get_db_session() as session:
        entry = (session.query(HydroDataEntry)
                 .options(joinedload(HydroDataEntry.run))
                 .where(HydroDataEntry.id == entry_id)
                 .first())

        if entry:
            session.expunge(entry)
        return entry


def update_entry(entry):
    """Update a single entry"""
    with get_db_session() as session:
        # Merge the entry into the current session
        merged_entry = session.merge(entry)
        session.expunge(merged_entry)
        return merged_entry


def sync_edited_data(edited_df: pd.DataFrame, original_df: pd.DataFrame):
    """
    Syncs edited DataFrame with the database, handling updates, new entries, and deletions
    """
    if edited_df.empty:
        return

    try:
        with get_db_session() as session:
            # Convert date columns to datetime if they're strings
            if 'date' in edited_df.columns and edited_df['date'].dtype == 'object':
                edited_df['date'] = pd.to_datetime(edited_df['date'])

            # Handle updates for existing entries
            for idx, row in edited_df.iterrows():
                if pd.isna(row['id']):  # New entry
                    new_entry = get_entry_from_df(row)
                    session.add(new_entry)
                else:  # Existing entry
                    original_row = original_df[original_df['id'] == row['id']].iloc[0] if not original_df[
                        original_df['id'] == row['id']].empty else None

                    if original_row is not None and not row.equals(original_row):
                        entry = session.query(HydroDataEntry).filter_by(id=int(row['id'])).first()
                        if entry:
                            for column in edited_df.columns:
                                if column != 'id':
                                    setattr(entry, column, row[column])

            # Handle deleted entries
            edited_ids = set(edited_df['id'].dropna().astype(int))
            original_ids = set(original_df['id'].dropna().astype(int))
            deleted_ids = original_ids - edited_ids

            if deleted_ids:
                for deleted_id in deleted_ids:
                    entry_to_delete = session.query(HydroDataEntry).filter_by(id=deleted_id).first()
                    if entry_to_delete:
                        session.delete(entry_to_delete)

        st.success('Successfully saved changes to database!')
    except Exception as e:
        st.error(f'Error saving to database: {str(e)}')
        raise