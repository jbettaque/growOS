import streamlit as st
from streamlit_local_storage import LocalStorage

st.title("Settings")
settings_form = st.form(key="settings_form")

local_storage = LocalStorage()

with settings_form:
    username = settings_form.text_input("Username")
    submit = settings_form.form_submit_button("Submit")

    if submit:
        local_storage.setItem("username", username)

summary_container = st.container(border=True)
with summary_container:
    st.subheader("Current Settings Summary")
    st.write("Username: " + local_storage.getItem("username"))