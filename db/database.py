import streamlit as st
from sqlalchemy.ext.declarative import declarative_base
from streamlit_sqlalchemy import StreamlitAlchemyMixin
from contextlib import contextmanager
from sqlalchemy.pool import QueuePool


Base = declarative_base()

# Initialize the connection with improved pool settings
conn = st.connection("hydro_db", type="sql")

StreamlitAlchemyMixin.st_initialize(connection=conn)

@contextmanager
def get_db_session():
    """
    Context manager for database sessions to ensure proper handling of connections.
    """
    session = None
    try:
        session = conn.session
        yield session
        session.commit()
    except Exception as e:
        if session:
            session.rollback()
        raise e
    finally:
        if session:
            session.close()

def init_db():
    Base.metadata.create_all(conn.engine)