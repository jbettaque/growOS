from sqlalchemy import Column, Integer, String, Date, Text
from sqlalchemy.orm import relationship
from db.database import Base
from streamlit_sqlalchemy import StreamlitAlchemyMixin

class HydroRun(Base, StreamlitAlchemyMixin):
    __tablename__ = "hydro_run"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    description = Column(Text)
    username = Column(String)

    entries = relationship("HydroDataEntry", back_populates="run")

    def __repr__(self):
        return f"{self.name}: {self.start_date} - {self.end_date or 'In progress'}"