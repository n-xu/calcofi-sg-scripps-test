"""
seed.py — Run once to create and populate the CalCOFI database.
Usage: python seed.py
"""

import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Station, DataType, StationDataLink

DATABASE_URL = "sqlite:///./calcofi.db"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# CTD cruise date ranges from uploaded cast files (2023-2025)
CTD_CRUISES = [
    ("2023-01-01", "2023-01-31"),
    ("2023-04-01", "2023-04-30"),
    ("2023-07-01", "2023-07-31"),
    ("2023-11-01", "2023-11-30"),
    ("2024-01-01", "2024-01-31"),
    ("2024-04-01", "2024-04-30"),
    ("2024-08-01", "2024-08-31"),
    ("2024-11-01", "2024-11-30"),
    ("2025-01-01", "2025-01-31"),
    ("2025-02-01", "2025-02-28"),
    ("2025-04-01", "2025-04-30"),
    ("2025-07-01", "2025-07-31"),
    ("2025-11-01", "2025-11-30"),
]
CTD_DATE_START = CTD_CRUISES[0][0]
CTD_DATE_END   = CTD_CRUISES[-1][1]

# Direct download URLs confirmed from calcofi.org/downloads/
# CTD prelim file pattern: calcofi.org/downloads/YYYY/20-YYMMSS_CTDPrelim.zip
# Most recent confirmed cruise: 2601RL (Jan 2026)
CTD_PRELIM_URL    = "https://calcofi.org/downloads/2024/20-2401RL_CTDPrelim.zip"
CTD_DATABASE_2019 = "https://calcofi.org/downloads/database/CTD/2009-2012_ctddb.zip"

SOURCE_META = {
    "CTD": {
        "url":   CTD_PRELIM_URL,
        "start": CTD_DATE_START,
        "end":   CTD_DATE_END,
        "fmt":   "ZIP (CSV)",
        "note":  "CTD preliminary data — most recent cruise (2401RL). Contains up & downcast CSVs for all stations.",
    },
    "Bottle DB": {
        "url":   "https://calcofi.org/downloads/database/CalCOFI_Database_194903-202105_csv_16October2023.zip",
        "start": "1949-03-01",
        "end":   "2021-05-31",
        "fmt":   "ZIP (CSV)",
        "note":  "Complete Bottle Database 1949–2021. Cast + Bottle tables as CSV.",
    },
    "DIC": {
        "url":   "https://calcofi.org/downloads/database/CalCOFI_DICs_200901-201507_28June2018.zip",
        "start": "2009-01-01",
        "end":   "2015-07-31",
        "fmt":   "ZIP (CSV)",
        "note":  "DIC data 2009–2015. For more recent DIC data visit the DIC data page.",
    },
    "Underway": {
        "url":   "https://calcofi.org/data/oceanographic-data/underway/",
        "start": "1990-01-01",
        "end":   "2025-12-31",
        "fmt":   "CSV",
        "note":  "Underway MET data — no single bulk download available. Visit data page to access by cruise.",
    },
    "Zooplankton": {
        "url":   "https://calcofi.org/downloads/database/195101-201607_1701-1704_1802-1804_Zoop.zip",
        "start": "1951-01-01",
        "end":   "2018-04-30",
        "fmt":   "ZIP (CSV)",
        "note":  "Zooplankton wet displacement volume CSV 1951–2018 (starboard bongo net).",
    },
    "Fish Eggs & Larvae": {
        "url":   "https://calcofi.org/data/marine-ecosystem-data/fish-eggs-larvae/",
        "start": "1951-01-01",
        "end":   "2025-12-31",
        "fmt":   "CSV",
        "note":  "Fish egg & larvae data available via NOAA IchthyoDB. Visit data page for access.",
    },
    "Phytoplankton": {
        "url":   "https://calcofi.org/data/marine-ecosystem-data/phytoplankton-bacterioplankton/",
        "start": "1980-01-01",
        "end":   "2025-12-31",
        "fmt":   "CSV",
        "note":  "Phytoplankton & bacterioplankton data — visit data page for download links.",
    },
    "Primary Production": {
        "url":   "https://calcofi.org/data/marine-ecosystem-data/primary-production/",
        "start": "1984-01-01",
        "end":   "2025-12-31",
        "fmt":   "CSV",
        "note":  "Primary production C14 data — visit data page for download links.",
    },
    "Marine Mammals": {
        "url":   "https://calcofi.org/data/marine-ecosystem-data/marine-mammals/",
        "start": "1991-01-01",
        "end":   "2025-12-31",
        "fmt":   "CSV",
        "note":  "Observed during transit between stations — not collected at fixed station points.",
    },
    "Seabirds": {
        "url":   "https://calcofi.org/data/marine-ecosystem-data/seabirds/",
        "start": "1987-01-01",
        "end":   "2025-12-31",
        "fmt":   "CSV",
        "note":  "Observed during transit between stations — not collected at fixed station points.",
    },
    "Genomics/eDNA": {
        "url":   "https://calcofi.org/data/marine-ecosystem-data/e-dna/",
        "start": "2014-01-01",
        "end":   "2025-12-31",
        "fmt":   "CSV",
        "note":  "Collected at selected stations only (approx. 20-30 per cruise) since 2014.",
    },
}


def create_tables():
    Base.metadata.create_all(engine)
    print("✓ Tables created")


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


def load_data_types(session):
    with open("data/data_types.csv") as f:
        for row in csv.DictReader(f):
            existing = session.query(DataType).filter_by(name=row["name"]).first()
            if not existing:
                session.add(DataType(
                    name                = row["name"],
                    category            = row["category"],
                    description         = row["description"],
                    unit                = row["unit"],
                    source              = row["source"],
                    local_variable_name = row.get("local_variable_name", ""),
                    source_url          = row.get("source_url", ""),
                ))
    session.commit()
    print(f"✓ Loaded {session.query(DataType).count()} data types")


def get_station_subset(session, source, all_stations):
    """
    Return the list of station_ids that actually have data for each source.
    Based on CalCOFI sampling protocols documented at calcofi.org/sampling-info
    """
    def ids(predicate):
        return [s.station_id for s in all_stations if predicate(s)]

    if source in ("CTD", "Bottle DB", "Zooplankton", "Fish Eggs & Larvae"):
        # Collected at all standard stations including SCCOOS
        return ids(lambda s: True)

    elif source == "DIC":
        # ~14 stations per cruise on main lines at intermediate depths
        main_lines = {60.0, 66.7, 70.0, 73.3, 76.7, 80.0, 83.3, 86.7, 90.0, 93.3}
        dic_stas   = {30.0, 35.0, 45.0, 55.0, 70.0}
        return ids(lambda s: s.line in main_lines and s.station in dic_stas)

    elif source == "Primary Production":
        # 1 per LAN per day (~18-20 per cruise), core standard stations
        main_lines = {60.0, 66.7, 70.0, 73.3, 76.7, 80.0, 83.3, 86.7, 90.0, 93.3}
        pp_stas    = {35.0, 45.0, 55.0, 70.0}
        return ids(lambda s: s.line in main_lines and s.station in pp_stas)

    elif source == "Phytoplankton":
        # Selected core stations, primarily southern lines
        main_lines = {76.7, 80.0, 83.3, 86.7, 90.0, 93.3}
        return ids(lambda s: s.line in main_lines and s.station > 20.0)

    elif source == "Genomics/eDNA":
        # Selected stations since 2014, roughly southern core lines
        main_lines = {80.0, 83.3, 86.7, 90.0, 93.3}
        return ids(lambda s: s.line in main_lines and s.station > 20.0)

    elif source in ("Marine Mammals", "Seabirds", "Underway"):
        # Transit observations — not tied to fixed stations
        return []

    else:
        # Default: all stations
        return ids(lambda s: True)


def load_links(session):
    all_stations = session.query(Station).all()
    data_types   = session.query(DataType).all()

    links_added = 0
    for dt in data_types:
        meta           = SOURCE_META.get(dt.source, {})
        station_subset = get_station_subset(session, dt.source, all_stations)

        for station_id in station_subset:
            existing = session.query(StationDataLink).filter_by(
                station_id=station_id,
                data_type_id=dt.data_type_id,
            ).first()
            if not existing:
                session.add(StationDataLink(
                    station_id       = station_id,
                    data_type_id     = dt.data_type_id,
                    url              = meta.get("url", dt.source_url),
                    format           = meta.get("fmt", "CSV"),
                    date_range_start = meta.get("start", ""),
                    date_range_end   = meta.get("end", ""),
                    notes            = meta.get("note", ""),
                ))
                links_added += 1

    session.commit()
    print(f"✓ Loaded {links_added} station-data links")


if __name__ == "__main__":
    print("\n🌊 CalCOFI Portal — Seeding database...\n")
    create_tables()
    s = Session()
    load_stations(s)
    load_data_types(s)
    load_links(s)
    print("\n✅ Done! Database saved to calcofi.db\n")
