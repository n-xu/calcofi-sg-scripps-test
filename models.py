from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()

class Station(Base):
    __tablename__ = "stations"

    station_id  = Column(String, primary_key=True)
    line        = Column(Float)
    station     = Column(Float)
    lat         = Column(Float)
    lon         = Column(Float)
    description = Column(String, default="")
    is_active   = Column(Boolean, default=True)

    links = relationship("StationDataLink", back_populates="station")


class DataType(Base):
    __tablename__ = "data_types"

    data_type_id        = Column(Integer, primary_key=True, autoincrement=True)
    name                = Column(String, unique=True)
    category            = Column(String)
    description         = Column(String, default="")
    unit                = Column(String, default="")
    source              = Column(String, default="")
    local_variable_name = Column(String, default="")
    source_url          = Column(String, default="")  # canonical page URL for this data source

    links = relationship("StationDataLink", back_populates="data_type")


class StationDataLink(Base):
    __tablename__ = "station_data_links"

    link_id          = Column(Integer, primary_key=True, autoincrement=True)
    station_id       = Column(String, ForeignKey("stations.station_id"))
    data_type_id     = Column(Integer, ForeignKey("data_types.data_type_id"))
    url              = Column(String, default="")
    format           = Column(String, default="")
    date_range_start = Column(String, default="")
    date_range_end   = Column(String, default="")
    notes            = Column(String, default="")

    station   = relationship("Station", back_populates="links")
    data_type = relationship("DataType", back_populates="links")


DATABASE_URL = "sqlite:///./calcofi.db"
engine = sessionmaker(bind=create_engine(DATABASE_URL))
