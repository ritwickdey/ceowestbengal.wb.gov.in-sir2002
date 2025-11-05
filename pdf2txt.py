import os
import re
from pdf2image import convert_from_path
import pytesseract
from multiprocessing import Pool, cpu_count
from typing import List

from tqdm import tqdm

PDF_FOLDER = "pdfs"
OUTPUT_FOLDER = "output_txt"


def ensure_output_folder():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def pdf_to_txt_path(pdf_path: str) -> str:
    """Return the corresponding output text file path for a given PDF."""
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    return os.path.join(OUTPUT_FOLDER, f"{base}.txt")


def ocr_page(page_image):
    """Runs OCR on a single PDF page (for multiprocessing)."""
    return pytesseract.image_to_string(page_image,
                                       lang="ben",
                                       config="--psm 6")


def extract_text_from_pdf(pdf_path: str) -> str:
    """Convert PDF to text using Tesseract OCR (parallel per page)."""
    pages = convert_from_path(pdf_path, dpi=150)
    num_workers = max(1, min(cpu_count() * 2, len(pages)))

    with Pool(processes=num_workers) as pool:
        results: List[str] = pool.map(ocr_page, pages)

    return "\n".join(results)


def convert(pdf_path: str) -> str:
    """Check if the text file already exists. Convert only if needed."""
    txt_path = pdf_to_txt_path(pdf_path)
    start_time = os.times()
    print(f"🔄 Converting: {os.path.basename(pdf_path)}")
    text = extract_text_from_pdf(pdf_path)
    end_time = os.times()
    elapsed = end_time.elapsed - start_time.elapsed
    print(
        f"✅ Converted: {os.path.basename(pdf_path)} in {elapsed:.2f} seconds")
    with open(txt_path, "w+", encoding="utf-8") as f:
        f.write(text)


def covert_to_txt():
    """Convert all PDFs to text (skips already converted ones)."""
    ensure_output_folder()

    pdf_files = [
        os.path.join(PDF_FOLDER, f) for f in os.listdir(PDF_FOLDER)
        if f.lower().endswith(".pdf")
    ]

    def sort_key(s):
        nums = re.findall(r'\d+', s)
        return tuple(map(int, nums))

    pdf_files = sorted(pdf_files, key=sort_key)
    print(f"Total PDFs found: {len(pdf_files)}")

    pdf_list_to_convert = []
    for pdf_path in pdf_files:
        txt_path = pdf_to_txt_path(pdf_path)
        if os.path.exists(txt_path) and os.path.getsize(txt_path) > 10:
            print(
                f"✅ Skipping (already converted): {os.path.basename(pdf_path)}"
            )
            continue
        else:
            pdf_list_to_convert.append(pdf_path)

    # print(f"Total PDFs to convert: {len(pdf_list_to_convert)}")
    # for index, pdf_path in enumerate(pdf_list_to_convert, 1):
    #     print(f"\nProcessing file {index}/{len(pdf_list_to_convert)}")
    #     convert(pdf_path)

    for pdf_path in tqdm(
            pdf_list_to_convert,
            desc="Converting PDFs",
            unit="file",
    ):
        convert(pdf_path)


if __name__ == "__main__":
    covert_to_txt()
