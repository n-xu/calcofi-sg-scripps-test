"""
seed.py — ERDDAP-enabled database seeding
Usage: python seed.py
"""

import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Station, DataType, StationDataLink

DATABASE_URL = "sqlite:///./calcofi.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


# -----------------------------
# Helpers
# -----------------------------

def build_erddap_url(dataset):
    if not dataset:
        return ""
    return f"https://coastwatch.pfeg.noaa.gov/erddap/tabledap/{dataset}.html"


def parse_bool(val):
    if val is None:
        return True  # default to True
    return str(val).strip().lower() in ("true", "1", "yes")


# -----------------------------
# Create tables
# -----------------------------

def create_tables():
    Base.metadata.create_all(engine)
    print("✓ Tables created")


# -----------------------------
# Load stations
# -----------------------------

def load_stations(session):
    with open("data/stations.csv") as f:
        for row in csv.DictReader(f):
            station = Station(
                station_id  = row["station_id"],
                line        = float(row["line"]),
                station     = float(row["station"]),
                lat         = float(row["lat"]),
                lon         = float(row["lon"]),
                description = row["description"],
                is_active   = row["is_active"].lower() == "true",
            )
            session.merge(station)
    session.commit()
    print(f"✓ Loaded {session.query(Station).count()} stations")


# -----------------------------
# Load data types (NEW CSV)
# -----------------------------

def load_data_types(session):
    with open("data/data_types_erddap.csv") as f:
        for row in csv.DictReader(f):
            existing = session.query(DataType).filter_by(name=row["name"]).first()
            if existing:
                continue

            dataset = row.get("erddap_dataset", "").strip()
            external_url = row.get("external_url", "").strip()

            # Prefer ERDDAP if available, else external
            source_url = (
                build_erddap_url(dataset)
                if dataset
                else external_url
            )

            session.add(DataType(
                name                = row["name"],
                category            = row["category"],
                description         = "",
                unit                = "",
                source              = row["source"],
                local_variable_name = row.get("erddap_variable", ""),
                source_url          = source_url,
            ))

    session.commit()
    print(f"✓ Loaded {session.query(DataType).count()} data types")


# -----------------------------
# Station subset logic (kept, simplified)
# -----------------------------

def get_station_subset(source, all_stations, is_station_based):
    """
    Simplified logic:
    - If not station-based → no stations
    - Otherwise → assume all stations (can refine later)
    """

    if not is_station_based:
        return []

    return [s.station_id for s in all_stations]


# -----------------------------
# Load links (updated)
# -----------------------------

def load_links(session):
    session.query(StationDataLink).delete()
    session.commit()
    all_stations = session.query(Station).all()
    data_types   = session.query(DataType).all()

    # Reload CSV so we can access is_station_based
    csv_lookup = {}
    with open("data/data_types_erddap.csv") as f:
        for row in csv.DictReader(f):
            csv_lookup[row["name"]] = row

    links_added = 0

    for dt in data_types:
        row = csv_lookup.get(dt.name, {})
        is_station_based = parse_bool(row.get("is_station_based"))

# fallback: assume True if missing
        if "is_station_based" not in row:
            is_station_based = True

        station_subset = get_station_subset(
            dt.source,
            all_stations,
            is_station_based
        )

        for station_id in station_subset:
            existing = session.query(StationDataLink).filter_by(
                station_id=station_id,
                data_type_id=dt.data_type_id,
            ).first()

            if not existing:
                session.add(StationDataLink(
                    station_id       = station_id,
                    data_type_id     = dt.data_type_id,
                    url              = dt.source_url,
                    format           = "ERDDAP" if "erddap" in (dt.source_url or "") else "LINK",
                    date_range_start = "",
                    date_range_end   = "",
                    notes            = "",
                ))
                links_added += 1

    session.commit()
    print(f"✓ Loaded {links_added} station-data links")


# -----------------------------
# Run
# -----------------------------

if __name__ == "__main__":
    print("\n🌊 CalCOFI Portal — Seeding database...\n")

    create_tables()
    s = Session()

    load_stations(s)
    load_data_types(s)
    load_links(s)

    print("\n✅ Done!\n")