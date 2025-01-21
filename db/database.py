import streamlit as st
from sqlalchemy.ext.declarative import declarative_base
from streamlit_sqlalchemy import StreamlitAlchemyMixin


Base = declarative_base()

# Initialize the connection
conn = st.connection("hydro_db", type="sql")
StreamlitAlchemyMixin.st_initialize(connection=conn)

def init_db():
    Base.metadata.create_all(conn.engine)

