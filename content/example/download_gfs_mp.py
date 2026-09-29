import os
from concurrent.futures import ProcessPoolExecutor, as_completed
import requests
from datetime import date

# Configuration
MAX_PROCESSES = 3  # Adjust based on your connection speed and server limits
DOWNLOAD_DIR = "./downloads" # Directory where to put the files

# Automatically fetch today's date in YYYYMMDD format (e.g., "20260923")
TARGET_DATE = date.today().strftime("%Y%m%d")

# Base URL dynamically injects the current date
BASE_URL = f"https://noaa.gov.{TARGET_DATE}/00/atmos"
FILENAME_TEMPLATE = "gfs.t00z.pgrb2.0p25.f{:03d}"

# Dynamically generate the list of files to download
FILES_TO_DOWNLOAD = [
    {
        "url": BASE_URL,
        "filename": FILENAME_TEMPLATE.format(hour)
    }
    for hour in range(0, 16, 3) 
]


def download_file(file_info):
    """Downloads a single file streaming it in chunks to optimize memory."""
    url = file_info["url"]
    filename = file_info["filename"]
    save_path = os.path.join(DOWNLOAD_DIR, filename)

    try:
        # Stream the download to avoid loading huge files into memory all at once
        with requests.get(os.path.join(url,filename), stream=True, timeout=15) as response:
            response.raise_for_status()  # Check for HTTP errors (404, 500, etc.)

            with open(save_path, "wb") as file:
                for chunk in response.iter_content(
                    chunk_size=8192
                ):  # 8KB chunks
                    if chunk:
                        file.write(chunk)

        return f"Successfully downloaded: {filename}"

    except requests.exceptions.RequestException as e:
        return f"Failed to download {filename}. Error: {e}"
    except Exception as e:
        return f"An unexpected error occurred for {filename}: {e}"


def main():
    # Ensure destination directory exists
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    print(
        f"Starting download of {len(FILES_TO_DOWNLOAD)} files using {MAX_PROCESSES} processes...\n"
    )

    # Use ProcessPoolExecutor to handle concurrent downloads
    with ProcessPoolExecutor(max_workers=MAX_PROCESSES) as executor:
        # Submit all tasks to the executor
        future_to_url = {
            executor.submit(download_file, file): file
            for file in FILES_TO_DOWNLOAD
        }

        # Process results as they finish
        for future in as_completed(future_to_url):
            result_message = future.result()
            print(result_message)

    print("\nAll download processes completed.")


if __name__ == "__main__":
    main()
