from pygments.lexer import default
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Float, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from streamlit_sqlalchemy import StreamlitAlchemyMixin
import streamlit as st
import pandas as pd

from db.database import Base
from model.hydro_run import HydroRun


class HydroDataEntry(Base, StreamlitAlchemyMixin):
    __tablename__ = "hydro_data_entry"

    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    ph_initial = Column(Float, nullable=False)
    ec_initial = Column(Float, nullable=False)
    ph_final = Column(Float, nullable=False)
    ec_final = Column(Float, nullable=False)
    ph_down_added = Column(Float, default=0)
    ph_up_added = Column(Float, default=0)
    hydro_vega_added = Column(Float, default=0)
    hydro_flora_added = Column(Float, default=0)
    rhizotonic_added = Column(Float, default=0)
    boost_added = Column(Float, default=0)
    light_hours = Column(Integer, nullable=False)
    light_intensity = Column(Integer, nullable=False)
    other_actions = Column(Text)
    observations = Column(Text)
    comments = Column(Text)
    water_temp = Column(Float, default=0)  # in Celsius
    water_added = Column(Float, default=0)  # in Liters
    water_level = Column(Float, default=0)  # in cm from top
    humidity = Column(Float, default=0)  # in percentage
    air_temp = Column(Float, default=0)  # in Celsius

    run_id = Column(Integer, ForeignKey('hydro_run.id'), nullable=False)

    run = relationship("HydroRun", back_populates="entries")

    def __repr__(self):
        return f"<HydroDataEntry(date={self.date}, ph_initial={self.ph_initial}, ec_initial={self.ec_initial})>"

    def __df__(self):
        result_df = pd.DataFrame([{
            'date': self.date,
            'run_id': self.run_id,
            'ph_initial': self.ph_initial,
            'ec_initial': self.ec_initial,
            'ph_final': self.ph_final,
            'ec_final': self.ec_final,
            'ph_down_added': self.ph_down_added,
            'ph_up_added': self.ph_up_added,
            'hydro_vega_added': self.hydro_vega_added,
            'hydro_flora_added': self.hydro_flora_added,
            'boost_added': self.boost_added,
            'rhizotonic_added': self.rhizotonic_added,
            'light_hours': self.light_hours,
            'light_intensity': self.light_intensity,
            'other_actions': self.other_actions,
            'observations': self.observations,
            'comments': self.comments
        }])

        return result_df

def get_all_entries_df(entries):
    return pd.DataFrame([{
        'date': entry.date,
        'run_id': entry.run_id,
        'ph_initial': entry.ph_initial,
        'ec_initial': entry.ec_initial,
        'ph_final': entry.ph_final,
        'ec_final': entry.ec_final,
        'ph_down_added': entry.ph_down_added,
        'ph_up_added': entry.ph_up_added,
        'hydro_vega_added': entry.hydro_vega_added,
        'hydro_flora_added': entry.hydro_flora_added,
        'boost_added': entry.boost_added,
        'rhizotonic_added': entry.rhizotonic_added,
        'light_hours': entry.light_hours,
        'light_intensity': entry.light_intensity,
        'other_actions': entry.other_actions,
        'observations': entry.observations,
        'comments': entry.comments,
        'water_temp': entry.water_temp,
        'water_added': entry.water_added,
        'water_level': entry.water_level,
        'humidity': entry.humidity,
        'air_temp': entry.air_temp
    } for entry in entries])