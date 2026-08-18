import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Configuration
MAX_THREADS = 3  # Adjust based on your connection speed and server limits
DOWNLOAD_DIR = "./downloads" # Directory where to put the files

# Sample files to download
FILES_TO_DOWNLOAD = [
    {
        "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260817/00/atmos",
        "filename": "gfs.t00z.pgrb2.0p25.f000",
    },
    {
        "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260817/00/atmos",
        "filename": "gfs.t00z.pgrb2.0p25.f003",
    },
    {
        "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260817/00/atmos",
        "filename": "gfs.t00z.pgrb2.0p25.f006",
    },
        {
        "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260817/00/atmos",
        "filename": "gfs.t00z.pgrb2.0p25.f009",
    },
    {
        "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260817/00/atmos",
        "filename": "gfs.t00z.pgrb2.0p25.f012",
    },
    {
        "url": "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.20260817/00/atmos",
        "filename": "gfs.t00z.pgrb2.0p25.f015",
    },
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
        f"Starting download of {len(FILES_TO_DOWNLOAD)} files using {MAX_THREADS} threads...\n"
    )

    # Use ThreadPoolExecutor to handle concurrent downloads
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
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
