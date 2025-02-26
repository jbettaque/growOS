import streamlit as st
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime

from components.run_selector import run_selector
from db.database import conn
from db.database_handler import get_all_entries, sync_edited_data
from model.hydro_data_entry import get_entry_from_df, HydroDataEntry, get_all_entries_df


def get_changes(edited_df: pd.DataFrame, original_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame containing only the changed rows with their modifications.

    Args:
        edited_df: DataFrame from st.data_editor
        original_df: Original DataFrame before edits

    Returns:
        DataFrame with changes highlighted and only modified rows included
    """
    changes = []

    # Handle modified and new rows
    for idx, row in edited_df.iterrows():
        if pd.isna(row['id']):  # New entry
            changes.append({
                'status': 'New',
                'id': 'NEW',
                **{col: {'value': row[col], 'changed': True} for col in edited_df.columns if col != 'id'}
            })
        else:  # Check for modifications in existing entries
            original_row = original_df[original_df['id'] == row['id']].iloc[0] if not original_df[
                original_df['id'] == row['id']].empty else None

            if original_row is not None and not row.equals(original_row):
                change_dict = {'status': 'Modified', 'id': row['id']}
                for col in edited_df.columns:
                    if col != 'id':
                        changed = row[col] != original_row[col]
                        change_dict[col] = {
                            'value': row[col],
                            'changed': changed,
                            'original': original_row[col] if changed else None
                        }
                changes.append(change_dict)

    # Handle deleted rows
    edited_ids = set(edited_df['id'].dropna().astype(int))
    original_ids = set(original_df['id'].dropna().astype(int))
    deleted_ids = original_ids - edited_ids

    for deleted_id in deleted_ids:
        deleted_row = original_df[original_df['id'] == deleted_id].iloc[0]
        changes.append({
            'status': 'Deleted',
            'id': deleted_id,
            **{col: {'value': deleted_row[col], 'changed': True} for col in edited_df.columns if col != 'id'}
        })

    return changes




# Update your main Streamlit app:
def display_changes(changes):
    """
    Displays the changes in a formatted way using Streamlit components.
    """
    if not changes:
        st.info("No changes detected")
        return

    for change in changes:
        status_color = {
            'New': 'green',
            'Modified': 'orange',
            'Deleted': 'red'
        }[change['status']]

        with st.expander(f"{change['status']} Entry (ID: {change['id']})", expanded=True):
            cols = st.columns([1, 1, 1])

            # Column headers
            cols[0].markdown("**Field**")
            cols[1].markdown("**New Value**")
            cols[2].markdown("**Original Value**")

            # Display each changed field
            for field, details in change.items():
                if field not in ['status', 'id']:
                    if details['changed']:
                        cols[0].markdown(f"**{field}**")
                        cols[1].markdown(f"```{details['value']}```")
                        if change['status'] == 'Modified':
                            cols[2].markdown(f"```{details['original']}```")
                        else:
                            cols[2].markdown("*N/A*")


def main():
    st.set_page_config(layout="wide")

    selected_run = run_selector()

    try:
        # Get original data
        all_entries = get_all_entries()
        all_entries_df = get_all_entries_df(all_entries)

        # Show editor
        edited_df = st.data_editor(
            all_entries_df,
            num_rows="dynamic",
            key="hydro_data_editor"
        )

        # Get changes before saving
        changes = get_changes(edited_df, all_entries_df)

        # Show changes in a dedicated section
        st.markdown("---")
        st.subheader("Pending Changes")
        display_changes(changes)

        # Add a save button
        if st.button('Save Changes'):
            sync_edited_data(edited_df, all_entries_df)

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()