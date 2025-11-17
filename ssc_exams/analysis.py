import json
import csv
from collections import defaultdict
from pathlib import Path

INPUT_FILE = "parsed_candidates.json"
OUTPUT_JSON_FILE = "post_analytics.json"
OUTPUT_CSV_FILE = "post_analytics.csv"

def analyze_candidates(json_path: str):
    data = json.loads(Path(json_path).read_text())

    # Key: (gender, category, quota_subject)
    stats = defaultdict(lambda: {"total": 0, "with_exp": 0, "without_exp": 0})

    for item in data:
        gender = item.get("gender")
        category = 'GENERAL' if item.get("category") == 'GEN' else 'OTHERS'
        quota_subject = item.get("quota_subject")  # <-- Updated grouping key
        exp_score = item.get("experience_score", 0)

        key = (gender, category, quota_subject)

        stats[key]["total"] += 1
        if exp_score > 0:
            stats[key]["with_exp"] += 1
        else:
            stats[key]["without_exp"] += 1

    return stats


def save_json(stats, out_file):
    result = []
    for (gender, category, quota_subject), values in stats.items():
        result.append({
            "gender": gender,
            "category": category,
            "quota_subject": quota_subject,
            "total_count": values["total"],
            "with_experience": values["with_exp"],
            "without_experience": values["without_exp"],
        })

    Path(out_file).write_text(json.dumps(result, indent=2))
    print(f"JSON analytics saved to {out_file}")


def save_csv(stats, out_file):
    with open(out_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Gender",
            "Category",
            "Quota Subject",
            "Total Count",
            "With Experience",
            "Without Experience",
        ])

        for (gender, category, quota_subject), values in stats.items():
            writer.writerow([
                gender,
                category,
                quota_subject,
                values["total"],
                values["with_exp"],
                values["without_exp"],
            ])

    print(f"CSV analytics saved to {out_file}")


if __name__ == "__main__":
    stats = analyze_candidates(INPUT_FILE)
    save_json(stats, OUTPUT_JSON_FILE)
    save_csv(stats, OUTPUT_CSV_FILE)