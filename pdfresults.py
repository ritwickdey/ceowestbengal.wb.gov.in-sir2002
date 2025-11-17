import json
from PyPDF2 import PdfReader
from PyPDF2.generic import Destination


def pdf_index_to_json(pdf_path: str, json_path: str):
    reader = PdfReader(pdf_path)

    # ------------------------------------------
    # Helper: Extract text between page ranges
    # ------------------------------------------
    def extract_text_range(start_page, end_page):
        extracted = []
        for p in range(start_page, end_page):
            page_obj = reader.pages[p]
            extracted.append(page_obj.extract_text() or "")
        return "\n".join(extracted).strip()

    # ------------------------------------------
    # Parse outline into hierarchical tree
    # ------------------------------------------
    def parse_outline(outline_list):
        result = []
        last_item = None

        for element in outline_list:

            # Nested list = children of last node
            if isinstance(element, list):
                if last_item is not None:
                    last_item["children"] = parse_outline(element)
                continue

            # A bookmark node
            if isinstance(element, Destination):
                try:
                    page_num = reader.get_destination_page_number(element)
                except Exception:
                    page_num = None

                node = {
                    "title": element.title,
                    "page": page_num + 1 if page_num is not None else None,
                    "children": [],
                    "content": ""  # filled later
                }

                result.append(node)
                last_item = node

        return result

    # ------------------------------------------
    # Step 1: Parse outline raw structure
    # ------------------------------------------
    outline_root = reader.outline
    parsed = parse_outline(outline_root)

    # ------------------------------------------
    # Step 2: Flatten nodes to compute text ranges
    # ------------------------------------------
    flat_list = []

    def flatten(nodes):
        for node in nodes:
            flat_list.append(node)
            flatten(node["children"])

    flatten(parsed)

    # Sort by actual PDF page order
    flat_list.sort(key=lambda x: x["page"] or 999999)

    # ------------------------------------------
    # Step 3: Add text content for each node
    # ------------------------------------------
    total_pages = len(reader.pages)

    for i, node in enumerate(flat_list):
        start = (node["page"] - 1) if node["page"] else None

        # Last node → go until EOF
        if i == len(flat_list) - 1:
            end = total_pages
        else:
            # Next node's page
            next_page = flat_list[i + 1]["page"]
            end = (next_page - 1) if next_page else total_pages

        if start is not None:
            node["content"] = extract_text_range(start, end)
        else:
            node["content"] = ""

    # ------------------------------------------
    # Step 4: Write final JSON
    # ------------------------------------------
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False)

    return parsed


# Example:
# pdf_index_to_json("input.pdf", "index.json")

# Example:
pdf_index_to_json("results_pdfs/result001.pdf", "output.json")
