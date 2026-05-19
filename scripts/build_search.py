import json
from collections import defaultdict

INPUT_VARIABLES = "data/variables.json"

OUTPUT_INDEX = "data/search_index.json"


def normalize(text):

    return (
        str(text)
        .lower()
        .strip()
    )


with open(INPUT_VARIABLES) as f:

    variables = json.load(f)

search_index = defaultdict(set)

for v in variables:

    variable_id = v["variable_id"]

    terms = []

    terms.append(v.get("variable_name", ""))

    terms.append(v.get("display_name", ""))

    terms.extend(v.get("keywords", []))

    terms.extend(v.get("science_concepts", []))

    for term in terms:

        term = normalize(term)

        if not term:
            continue

        search_index[term].add(variable_id)

# convert sets -> sorted lists

final_index = {

    k: sorted(list(v))

    for k, v in search_index.items()
}

with open(OUTPUT_INDEX, "w") as f:

    json.dump(final_index, f, indent=2)

print(f"Wrote {len(final_index)} search terms")