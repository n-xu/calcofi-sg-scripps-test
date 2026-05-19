"""
main.py — CalCOFI Portal API
Run with: uvicorn main:app --reload
Docs at:  http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Station, DataType, StationDataLink

# --- Setup ---
DATABASE_URL = "sqlite:///./calcofi.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

app = FastAPI(title="CalCOFI Portal API")

# Allow frontend to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Routes ---

@app.get("/")
def root():
    return {"message": "CalCOFI Portal API is running 🌊"}


@app.get("/stations")
def get_all_stations():
    """Return all stations with coordinates — used to render map dots."""
    session = Session()
    stations = session.query(Station).order_by(Station.station_id).all()
    return [
        {
            "station_id":  s.station_id,
            "line":        s.line,
            "station":     s.station,
            "lat":         s.lat,
            "lon":         s.lon,
            "description": s.description,
            "is_active":   s.is_active,
        }
        for s in stations
    ]


@app.get("/stations/{station_id:path}")
def get_station(station_id: str):
    """Return a single station and all its data links — used when user clicks a station."""
    session = Session()
    station = session.query(Station).filter_by(station_id=station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail=f"Station '{station_id}' not found")

    links = (
        session.query(StationDataLink, DataType)
        .join(DataType, StationDataLink.data_type_id == DataType.data_type_id)
        .filter(StationDataLink.station_id == station_id)
        .all()
    )

    return {
        "station_id":  station.station_id,
        "line":        station.line,
        "station":     station.station,
        "lat":         station.lat,
        "lon":         station.lon,
        "description": station.description,
        "data": [
            {
                "name":             dt.name,
                "category":         dt.category,
                "unit":             dt.unit,
                "source":           dt.source,
                "local_variable":   dt.local_variable_name,
                "url":              link.url,
                "format":           link.format,
                "date_range_start": link.date_range_start,
                "date_range_end":   link.date_range_end,
                "notes":            link.notes,
            }
            for link, dt in links
        ],
    }


@app.get("/variables")
def get_variables(search: str = Query(default="", description="Search by variable name")):
    """
    Return all variables, optionally filtered by name search.
    Used for the search feature — also returns which stations have each variable.
    """
    session = Session()
    query = session.query(DataType)
    if search:
        query = query.filter(DataType.name.ilike(f"%{search}%"))
    data_types = query.order_by(DataType.category, DataType.name).all()

    results = []
    for dt in data_types:
        station_ids = [
            link.station_id
            for link in session.query(StationDataLink)
            .filter_by(data_type_id=dt.data_type_id)
            .all()
        ]
        results.append({
            "data_type_id":      dt.data_type_id,
            "name":              dt.name,
            "category":          dt.category,
            "unit":              dt.unit,
            "source":            dt.source,
            "local_variable":    dt.local_variable_name,
            "station_ids":       station_ids,
            "station_count":     len(station_ids),
        })

    return results


@app.get("/categories")
def get_categories():
    """Return all unique variable categories — used for filter buttons in the UI."""
    session = Session()
    categories = session.query(DataType.category).distinct().order_by(DataType.category).all()
    return [c[0] for c in categories]
