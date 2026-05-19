import simplejson
import pandas as pd

INPUT_CSV = "metadata/data_sources.csv"
OUTPUT_JSON = "data/datasets.json"

df = pd.read_csv(INPUT_CSV)

datasets = []

for _, row in df.iterrows():

    dataset = {
        "dataset_id": row["dataset_id"],
        "name": row["name"],
        "url": row["url"],
        "platform": row["platform"],
        "base_url": row["base_url"],
        "station_based": bool(row["station_based"]),
    }

    datasets.append(dataset)

with open(OUTPUT_JSON, "w") as f:
    simplejson.dump(datasets, f, indent=2, ignore_nan=True)

print(f"Wrote {len(datasets)} datasets")