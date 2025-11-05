import os
OUTPUT_FOLDER = "output_txt"

def search_bengali_text(search_text: str):
    """Search for Bengali text in all converted files."""
    matched_files = []

    for txt_file in os.listdir(OUTPUT_FOLDER):
        if txt_file.lower().endswith(".txt"):
            txt_path = os.path.join(OUTPUT_FOLDER, txt_file)
            with open(txt_path, "r", encoding="utf-8") as f:
                contents = f.read().splitlines()
                for content in contents:
                    if search_text in content:
                        matched_files.append({
                            "file": txt_path,
                            "line": content.strip()
                        })

    print("\n=== SUMMARY ===")
    if matched_files:
        print(f"✅ Found '{search_text}' in {len(matched_files)} file(s):")
        for f in matched_files:
            print(f"  • {os.path.basename(f['file'])}: {f['line']}")
    else:
        print(f"❌ No matches found for '{search_text}'.")


if __name__ == "__main__":
    # Example: user provides a Bengali phrase to search
    search_text = input("Enter Bengali text to search: ").strip()
    search_bengali_text(search_text)
