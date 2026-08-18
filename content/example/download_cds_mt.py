import cdsapi
import concurrent.futures
import os

# Initialize the Climate Data Store client
c = cdsapi.Client()

def download_era5_daily_avg(year, month):
    """Worker function to download daily average 2m temperature for a specific month/year."""
    # Ensure two-digit month format (e.g., '05' instead of '5')
    month_str = f"{month:02d}"
    output_filename = f"era5_daily_mean_t2m_{year}_{month_str}.nc"
    
    # Skip download if the file already exists
    if os.path.exists(output_filename):
        print(f"File {output_filename} already exists. Skipping.")
        return output_filename

    print(f"Submitting request for {year}-{month_str}...")
    
    try:
        # Request configuration targeting the post-processed daily statistics dataset
        c.retrieve(
            'derived-era5-single-levels-daily-statistics',
            {
                'product_type': 'reanalysis',
                'variable': '2m_temperature',
                'daily_statistic': 'daily_mean',           # Requests the pre-calculated daily average
                'time_zone': 'utc+00:00',                  # Calculate average based on UTC day boundary
                'frequency': '1_hour',                     # Use all 24 hourly steps to calculate the mean
                'year': str(year),
                'month': month_str,
                'day': [f"{d:02d}" for d in range(1, 32)], # Includes all valid days of the month
                'format': 'netcdf',
            },
            output_filename
        )
        print(f"Successfully downloaded: {output_filename}")
        return output_filename
    except Exception as e:
        print(f"Error downloading {year}-{month_str}: {e}")
        return None

def main():
    # Define your temporal target scope
    target_years = [2023, 2024, 2025]
    months = list(range(1, 13)) # Months 1 through 12
    
    # Create a list of task tuples: (year, month)
    download_tasks = [(y, m) for y in target_years for m in months]
    
    # Setting max_workers to 2 keeps the requests flowing perfectly into the server queue
    MAX_CONCURRENT_REQUESTS = 2
    
    print(f"Starting parallel download for {len(download_tasks)} month-long blocks...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT_REQUESTS) as executor:
        # Pass the task arguments into the parallel executor
        futures = [executor.submit(download_era5_daily_avg, year, month) for year, month in download_tasks]
        
        # Monitor threads as they wrap up
        for future in concurrent.futures.as_completed(futures):
            future.result()
        
    print("All parallel daily-average downloads have finished.")

if __name__ == "__main__":
    main()
