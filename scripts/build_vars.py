import json
import pandas as pd
import requests

INPUT_CSV = "metadata/data_sources.csv"

OUTPUT_JSON = "data/variables.json"


# =====================================================
# HELPERS
# =====================================================

def clean(value):

    if value is None:
        return ""

    return str(value).strip()


def make_variable_id(dataset_id, variable_name):

    safe = variable_name.replace(" ", "_")

    return f"{dataset_id}::{safe}"


def infer_entity_type(name):

    n = name.lower()

    if any(x in n for x in [
        "temp",
        "temperature",
        "salinity",
        "density"
    ]):
        return "physical_variable"

    if any(x in n for x in [
        "oxygen",
        "nitrate",
        "phosphate",
        "silicate",
        "ph"
    ]):
        return "chemical_variable"

    return "scientific_variable"


def build_info_url(base_url, dataset_id):

    base = base_url.rstrip("/")

    return (
        f"{base}/erddap/info/"
        f"{dataset_id}/index.json"
    )


# =====================================================
# PARSE ERDDAP INFO JSON
# =====================================================

def parse_erddap_info(metadata_json):

    rows = metadata_json["table"]["rows"]

    variables = {}

    current_variable = None

    for row in rows:

        row_type = row[0]

        variable_name = clean(row[1])

        attribute_name = clean(row[2])

        value = clean(row[4])

        # ---------------------------------------------
        # VARIABLE ROW
        # ---------------------------------------------

        if row_type == "variable":

            current_variable = variable_name

            variables[current_variable] = {

                "variable_name":
                    current_variable,

                "display_name":
                    current_variable,

                "description":
                    "",

                "units":
                    "",

                "ioos_category":
                    "",

                "long_name":
                    ""
            }

        # ---------------------------------------------
        # ATTRIBUTE ROW
        # ---------------------------------------------

        elif row_type == "attribute":

            if variable_name not in variables:
                continue

            if attribute_name == "description":

                variables[variable_name]["description"] = value

            elif attribute_name == "units":

                variables[variable_name]["units"] = value

            elif attribute_name == "long_name":

                variables[variable_name]["long_name"] = value

            elif attribute_name == "ioos_category":

                variables[variable_name]["ioos_category"] = value

    return list(variables.values())


# =====================================================
# LOAD DATA SOURCES
# =====================================================

df = pd.read_csv(INPUT_CSV)

all_variables = []

# =====================================================
# PROCESS DATASETS
# =====================================================

for _, row in df.iterrows():

    dataset_id = clean(row["dataset_id"])

    dataset_name = clean(row["name"])

    platform = clean(row["platform"]).lower()

    access_url = clean(row["url"])

    base_url = clean(row["base_url"])

    station_based = bool(row["station_based"])

    print(f"\nProcessing: {dataset_id}")

    # =================================================
    # ERDDAP
    # =================================================

    if platform == "erddap":

        metadata_url = build_info_url(
            base_url,
            dataset_id
        )

        print("Metadata URL:")
        print(metadata_url)

        try:

            response = requests.get(metadata_url)

            metadata_json = response.json()

        except Exception as e:

            print("FAILED:", dataset_id)
            print(e)

            continue

        parsed_variables = parse_erddap_info(
            metadata_json
        )

        print(
            f"Found {len(parsed_variables)} variables"
        )

        for pv in parsed_variables:

            variable_name = pv["variable_name"]

            display_name = (
                pv["long_name"]
                or variable_name
            )

            description = pv["description"]

            units = pv["units"]

            ioos_category = pv["ioos_category"]

            variable = {

                "variable_id":
                    make_variable_id(
                        dataset_id,
                        variable_name
                    ),

                "dataset_id":
                    dataset_id,

                "dataset_name":
                    dataset_name,

                "entity_type":
                    infer_entity_type(
                        variable_name
                    ),

                "variable_name":
                    variable_name,

                "display_name":
                    display_name,

                "description":
                    description,

                "units":
                    units,

                "platform":
                    platform,

                "station_based":
                    station_based,

                "station_ids":
                    [],

                "science_concepts":
                    [ioos_category]
                    if ioos_category else [],

                "keywords":
                    list(set([
                        variable_name,
                        display_name,
                        description,
                        ioos_category
                    ])),

                "taxonomy":
                    {},

                "source": {

                    "access_url":
                        access_url,

                    "metadata_url":
                        metadata_url
                }
            }

            all_variables.append(variable)

    # =================================================
    # NON-ERDDAP
    # =================================================

    else:

        all_variables.append({

            "variable_id":
                f"{dataset_id}::dataset",

            "dataset_id":
                dataset_id,

            "dataset_name":
                dataset_name,

            "entity_type":
                "scientific_dataset",

            "variable_name":
                dataset_name,

            "display_name":
                dataset_name,

            "description":
                dataset_name,

            "units":
                "",

            "platform":
                platform,

            "station_based":
                station_based,

            "station_ids":
                [],

            "science_concepts":
                [],

            "keywords":
                [dataset_name],

            "taxonomy":
                {},

            "source": {

                "access_url":
                    access_url,

                "metadata_url":
                    ""
            }
        })


# =====================================================
# EUPHAUSIID SPECIES
# =====================================================

EUPHAUSIA_FILE = "metadata/euphausia.txt"

try:

    with open(EUPHAUSIA_FILE) as f:

        species_list = [

            x.strip()

            for x in f.readlines()

            if x.strip()
        ]

    print(
        f"\nAdding {len(species_list)} euphausiid species"
    )

    for species in species_list:

        parts = species.split()

        genus = (
            parts[0].capitalize()
            if len(parts) > 0 else ""
        )

        species_name = (
            parts[1]
            if len(parts) > 1 else ""
        )

        canonical_name = (
            f"{genus} {species_name}"
        ).strip()

        variable = {

            "variable_id":
                f"euphausiid::{canonical_name.replace(' ', '_')}",

            "dataset_id":
                "euphausiid",

            "dataset_name":
                "CalCOFI Euphausiid Database",

            "entity_type":
                "taxon",

            "variable_name":
                canonical_name,

            "display_name":
                canonical_name,

            "description":
                "Euphausiid species observation",

            "units":
                "count",

            "platform":
                "oceaninformatics",

            "provider":
                "SIO",

            "station_based":
                True,

            "station_ids":
                [],

            "science_concepts": [
                "zooplankton",
                "krill",
                "euphausiids"
            ],

            "keywords": list(set([

                canonical_name,

                genus,

                "krill",
                "euphausiid",
                "zooplankton"
            ])),

            "taxonomy": {

                "kingdom":
                    "Animalia",

                "phylum":
                    "Arthropoda",

                "class":
                    "Malacostraca",

                "order":
                    "Euphausiacea",

                "genus":
                    genus,

                "species":
                    species_name
            },

            "source": {

                "access_url":
                    "https://oceaninformatics.ucsd.edu/euphausiid/",

                "metadata_url":
                    ""
            }
        }

        all_variables.append(variable)

except Exception as e:

    print("\nFailed euphausiid ingestion")
    print(e)


# =====================================================
# ZOODB TAXA
# =====================================================

ZOODB_FILE = "metadata/zoodb.csv"

try:

    zoodb_df = pd.read_csv(ZOODB_FILE)

    print(
        f"\nAdding {len(zoodb_df)} ZooDB taxa"
    )

    for _, row in zoodb_df.iterrows():

        higher_taxonomy = str(
            row["higher_taxa"]
        ).strip()

        genus_species = str(
            row["genus_species"]
        ).strip()

        if not genus_species:
            continue

        parts = genus_species.split()

        genus = (
            parts[0]
            if len(parts) > 0 else ""
        )

        species_name = (
            parts[1]
            if len(parts) > 1 else ""
        )

        variable = {

            "variable_id":
                f"zoodb::{genus_species.replace(' ', '_')}",

            "dataset_id":
                "zoodb",

            "dataset_name":
                "CalCOFI ZooDB",

            "entity_type":
                "taxon",

            "variable_name":
                genus_species,

            "display_name":
                genus_species,

            "description":
                "Zooplankton taxonomic observation",

            "units":
                "count",

            "platform":
                "oceaninformatics",

            "provider":
                "SIO",

            "station_based":
                True,

            "station_ids":
                [],

            "science_concepts": [
                "zooplankton"
            ],

            "keywords": list(set([

                genus_species,

                genus,

                higher_taxonomy,

                "zooplankton"
            ])),

            "taxonomy": {

                "higher_taxonomy":
                    higher_taxonomy,

                "genus":
                    genus,

                "species":
                    species_name
            },

            "source": {

                "access_url":
                    "https://oceaninformatics.ucsd.edu/zoodb/",

                "metadata_url":
                    ""
            }
        }

        all_variables.append(variable)

except Exception as e:

    print("\nFailed ZooDB ingestion")
    print(e)

# =====================================================
# WRITE OUTPUT
# =====================================================

with open(OUTPUT_JSON, "w") as f:

    json.dump(
        all_variables,
        f,
        indent=2
    )

print("\n================================")
print(f"Wrote {len(all_variables)} variables")
print("================================")