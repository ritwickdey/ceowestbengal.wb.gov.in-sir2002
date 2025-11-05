import os
import base64
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Event

# === CONFIGURATION ===
acid = 211
folder_name = "pdfs"     # folder name as variable
max_workers = 2               # number of concurrent downloads
timeout = 20                  # seconds per request

# === SETUP ===
os.makedirs(folder_name, exist_ok=True)
print(f"📂 Downloading PDFs for ACID {acid} into folder '{folder_name}'...\n")

# Shared event for stopping all threads when one 404 is hit
stop_event = Event()

def download_pdf(part_num):
    """Download a single part, skipping if exists or stopping if 404."""
    if stop_event.is_set():
        return None  # stop immediately if flagged

    part_str = f"PART{part_num:03d}"
    filename = f"AC{acid}{part_str}.pdf"
    filepath = os.path.join(folder_name, filename)

    # Skip if file already exists
    if os.path.exists(filepath):
        return f"⏩ Skipped (exists): {filename}"

    # Construct base64 key and URL
    encoded_key = base64.b64encode(filename.encode()).decode()
    url = f"https://ceowestbengal.wb.gov.in/RollPDF/GetDraft?acId={acid}&key={encoded_key}"

    try:
        response = requests.get(url, timeout=timeout)

        # Stop condition: file not found
        if response.status_code == 404:
            stop_event.set()  # signal all threads to stop
            return f"🚫 {filename} not found (404) — stopping."

        response.raise_for_status()

        # Save PDF
        with open(filepath, "wb") as f:
            f.write(response.content)

        return f"✅ Downloaded: {filename}"

    except requests.exceptions.RequestException as e:
        return f"❌ Error for {filename}: {e}"

def main():
    part_num = 1

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}

        while not stop_event.is_set():
            # Submit next batch of jobs
            for i in range(max_workers):
                if stop_event.is_set():
                    break
                futures[executor.submit(download_pdf, part_num)] = part_num
                part_num += 1

            # Process completed futures
            for future in as_completed(futures):
                result = future.result()
                if result:
                    print(result)
            futures.clear()

    print("\n✅ Completed. All available files downloaded into:", folder_name)

if __name__ == "__main__":
    main()
