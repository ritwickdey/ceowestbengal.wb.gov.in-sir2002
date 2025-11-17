import json
import csv
from pathlib import Path

def json_to_csv(json_path: str, csv_path: str) -> None:
    json_file = Path(json_path)

    with json_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be a list of objects.")

    # Collect all keys (even if some rows don't have all keys)
    keys = set()
    for item in data:
        keys.update(item.keys())

    keys = sorted(keys)

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)

    print(f"CSV saved to {csv_path}")


if __name__ == "__main__":
    json_to_csv("parsed_candidates.json", "output.csv")
