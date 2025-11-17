import json
import re
from pathlib import Path


# ---------------------------------------------------------
# Clean title for XPath
# ---------------------------------------------------------
def clean_title(title: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", title).strip("-")


# ---------------------------------------------------------
# Parse one candidate block
# ---------------------------------------------------------
def parse_candidate_block(block: str):
    lines = [l.strip() for l in block.strip().split("\n") if l.strip()]

    name = lines[0]  # first line is name
    text = " ".join(lines[1:]).replace("  ", " ")

    pattern = (
        r"(?P<dob>\d{2}-\d{2}-\d{4})"
        r"(?P<gender>MALE|FEMALE)"
        r"\s*(?P<category>GEN|SC|ST|OBC-A|OBC-B)"
        r"\s*(?P<total_score>\d+)"
        r"\s*(?P<rank>[A-Z0-9\-]+)"
        r"\s*(?P<roll_no>\d+)"
        r"\s*\d*\s*"                
        r"(?P<score>\d+)"
        r"\s*(?P<subject_score>\d+)"
        r"\s*(?P<experience_score>\d+)"
    )

    m = re.search(pattern, text)
    if not m:
        return None

    return {
        "name": name,
        "dob": m.group("dob"),
        "gender": m.group("gender"),
        "category": m.group("category"),
        "total_score": int(m.group("total_score")),
        "rank": m.group("rank"),
        "roll_no": m.group("roll_no"),
        "score": int(m.group("score")),
        "subject_score": int(m.group("subject_score")),
        "experience_score": int(m.group("experience_score")),
    }


# ---------------------------------------------------------
# Split content into blocks based on NAME lines
# ---------------------------------------------------------
def split_into_blocks(content: str):
    blocks = []
    current = []

    for line in content.split("\n"):
        if re.fullmatch(r"[A-Z][A-Z ]+", line.strip()):
            if current:
                blocks.append("\n".join(current))
                current = []
        if line.strip():
            current.append(line)

    if current:
        blocks.append("\n".join(current))

    return blocks


# Parse all candidates from content
def parse_section(content: str):
    blocks = split_into_blocks(content)
    parsed = []

    for block in blocks:
        x = parse_candidate_block(block)
        if x:
            parsed.append(x)

    return parsed


# ---------------------------------------------------------
# MAIN: Walk the nested JSON and produce records with XPATH
# ---------------------------------------------------------
def parse_output_json(input_json: str, output_json: str):
    raw = Path(input_json).read_text(encoding="utf-8")
    data = json.loads(raw)

    all_records = []

    def walk(node, path_components):
        clean_path = "/".join(path_components[1:])  # remove root

        # --------------------------------------------------
        # If this node has content → parse candidates
        # --------------------------------------------------
        if isinstance(node, dict) and "content" in node and isinstance(node["content"], str):

            section_records = parse_section(node["content"])

            for rec in section_records:
                # Attach the raw xpath
                rec["xpath"] = clean_path

                # --------------------------------------------------
                # VALIDATOR: total_score == score + subject + exp
                # --------------------------------------------------
                calc_total = rec["score"] + rec["subject_score"] + rec["experience_score"]
                rec["valid"] = (calc_total == rec["total_score"])

                # --------------------------------------------------
                # XPATH PARSER: extract subject, medium, category, gender
                # --------------------------------------------------
                parts = clean_path.split("/")

                # Ensure enough components exist
                quota_subject = parts[0] if len(parts) > 0 else None
                quota_medium = parts[1] if len(parts) > 1 else None
                quota_category = parts[2] if len(parts) > 2 else None
                quota_gender = parts[3] if len(parts) > 3 else None

                rec["quota_subject"] = quota_subject
                rec["quota_medium"] = quota_medium
                rec["quota_category"] = quota_category
                rec["quota_gender"] = quota_gender

                all_records.append(rec)

        # --------------------------------------------------
        # Recurse children
        # --------------------------------------------------
        if isinstance(node, dict) and "children" in node:
            for child in node["children"]:
                child_title = clean_title(child.get("title", ""))
                walk(child, path_components + [child_title])

    # --------------------------------------------------
    # ROOT FIX: support both list and dict
    # --------------------------------------------------
    if isinstance(data, list):
        for root in data:
            root_title = clean_title(root.get("title", "root"))
            walk(root, [root_title])
    else:
        root_title = clean_title(data.get("title", "root"))
        walk(data, [root_title])

    # Save final output
    Path(output_json).write_text(
        json.dumps(all_records, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Done. Parsed {len(all_records)} candidates → {output_json}")


# ---------------------------------------------------------
# Run if executed directly
# ---------------------------------------------------------
if __name__ == "__main__":
    parse_output_json("output.json", "parsed_candidates.json")
