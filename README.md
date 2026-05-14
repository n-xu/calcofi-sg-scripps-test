# CalCOFI Station Data Portal

An interactive map-based portal for exploring oceanographic and marine ecosystem data collected at CalCOFI stations along the California coast.

Built as part of the PSTAT 197 Capstone project in collaboration with CalCOFI, SeaGrant, and Scripps Institution of Oceanography.

---

## What It Does

- **Interactive map** of 115 real CalCOFI stations with clickable markers
- **Station panel** — click any station to see all data collected there, grouped by source (CTD, Bottle DB, Zooplankton, etc.)
- **Direct downloads** — download CTD cruise files by year, Bottle Database, DIC, Zooplankton, and the full LTER Master Database
- **Search & filter** — live dropdown search by variable name, filter by category (Physical, Chemical, Biological, etc.)
- **Accurate highlighting** — searching a variable highlights only the stations where that data is actually collected
- **Download All** — one-click access to the full CalCOFI LTER Master Database (1949–2023)

---

## Data Sources

| Source | Stations | Date Range | Direct Download? |
|---|---|---|---|
| CTD Cast Files | All 115 | 2020–2024 | ✅ Per-cruise zip |
| Bottle Database | All 115 | 1949–2021 | ✅ Full CSV zip |
| DIC | ~25 | 2009–2015 | ✅ Direct zip |
| Zooplankton | All 115 | 1951–2018 | ✅ Direct zip |
| Fish Eggs & Larvae | All 115 | 1951–present | 🔗 Data page |
| Primary Production | ~23 | 1984–present | 🔗 Data page |
| Phytoplankton | ~56 | 1980–present | 🔗 Data page |
| Genomics/eDNA | ~49 | 2014–present | 🔗 Data page |
| Marine Mammals | Transit only | 1991–present | 🔗 Data page |
| Seabirds | Transit only | 1987–present | 🔗 Data page |
| Underway MET | Transit only | 1990–present | 🔗 Data page |

---

## Project Structure

```
calcofi-portal/
├── models.py          # SQLAlchemy database models (stations, data_types, links)
├── seed.py            # Builds and populates the database from CSVs
├── main.py            # FastAPI backend — 4 REST endpoints
├── map.html           # Frontend — standalone HTML map (open in browser)
├── data/
│   ├── stations.csv   # 115 real CalCOFI stations with lat/lon
│   └── data_types.csv # 111 variables across all 11 data sources
└── README.md
```

> `calcofi.db` is not included in the repo — it is generated locally by running `seed.py`.

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- pip

### 1. Clone the repo

```bash
git clone https://github.com/pstat197/capstone-calcofi-seagrant-scripps.git
cd capstone-calcofi-seagrant-scripps
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy
```

### 4. Build the database

```bash
python seed.py
```

You should see:
```
✓ Tables created
✓ Loaded 115 stations
✓ Loaded 111 data types
✓ Loaded 11184 station-data links
✅ Done! Database saved to calcofi.db
```

### 5. Start the API

```bash
uvicorn main:app --reload
```

The API will be running at `http://localhost:8000`

### 6. Open the map

Double-click `map.html` in Finder (Mac) or File Explorer (Windows) to open it in your browser.

---

## API Endpoints

| Endpoint | Description |
|---|---|
| `GET /stations` | All 115 stations with lat/lon — powers the map dots |
| `GET /stations/{id}` | Single station with all its data links |
| `GET /variables?search=chlorophyll` | Search variables by name |
| `GET /categories` | All variable categories (Physical, Chemical, etc.) |

Interactive API docs available at `http://localhost:8000/docs` while the server is running.

---

## Updating the Data

### Adding new stations or variables

Edit `data/stations.csv` or `data/data_types.csv` directly (they open in Excel), then rebuild the database:

```bash
rm calcofi.db
python seed.py
```

### Adding new CTD cruise download links

In `seed.py`, find the `CTD_CRUISES` list in `map.html` and add a new entry following the pattern:

```javascript
{ label: '2025 Jan (2501RL)', url: 'https://calcofi.org/downloads/2025/20-2501RL_CTDPrelim.zip' },
```

CTD preliminary files follow the URL pattern:
```
https://calcofi.org/downloads/YYYY/20-YYMMSS_CTDPrelim.zip
```

---

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **Frontend**: Vanilla HTML/CSS/JS, Leaflet.js
- **Data**: CalCOFI public datasets (calcofi.org/data)

---

## Data Use Agreement

All CalCOFI data is publicly available. By downloading you accept the [CalCOFI data use agreement](https://calcofi.org/data/data-usage-policy/).

---

## Contact

For data questions: calcofi@gmail.com  
For project questions: PSTAT 197 Capstone — UC Santa Barbara
