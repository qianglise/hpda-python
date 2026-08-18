import duckdb
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import random

# ==========================================
# 1. Setup Database Connection & Table
# ==========================================
duckdb_con = duckdb.connect('my_peristent_db.duckdb')

duckdb_con.execute("""
    CREATE OR REPLACE TABLE my_inserts (
        thread_name VARCHAR,
        insert_time TIMESTAMP DEFAULT current_timestamp
    )
""")


# ==========================================
# 2. Worker Tasks (Writer & Reader)
# ==========================================
def write_task(duckdb_con, task_id):
    # Create a unique, thread-safe cursor from the main connection
    local_con = duckdb_con.cursor()
    
    # Track the underlying OS thread name alongside the task ID
    thread_name = f"writer_task_{task_id} ({threading.current_thread().name})"
    
    local_con.execute("""
        INSERT INTO my_inserts (thread_name) VALUES (?)
    """, (thread_name,))
    return f"Task {task_id} successfully inserted data."


def read_task(duckdb_con, task_id):
    # Create a unique, thread-safe cursor from the main connection
    local_con = duckdb_con.cursor()
    
    thread_name = f"reader_task_{task_id} ({threading.current_thread().name})"
    results = local_con.execute("""
        SELECT ? AS worker, count(*) AS row_counter, current_timestamp 
        FROM my_inserts
    """, (thread_name,)).fetchall()
    
    return results


# ==========================================
# 3. Queue Tasks and Execute with ThreadPool
# ==========================================
write_task_count = 5
read_task_count = 5

# Prepare the collection of callable functions and their arguments
tasks = []

for i in range(write_task_count):
    tasks.append((write_task, (duckdb_con, i)))

for j in range(read_task_count):
    tasks.append((read_task, (duckdb_con, j)))

# Shuffle tasks to mix reader and writer execution order randomly
random.seed(6)
random.shuffle(tasks)

# Execute via ThreadPoolExecutor
# max_workers can be tuned based on your machine's hardware capabilities
with ThreadPoolExecutor(max_workers=5) as executor:
    # Submit all shuffled operations to the thread pool
    futures = [executor.submit(func, *args) for func, args in tasks]
    
    # Process results dynamically as they complete
    for future in as_completed(futures):
        try:
            result = future.result()
            # If it's a reader task (returns a list), print it out
            if isinstance(result, list):
                print(f"Reader Result: {result}")
        except Exception as e:
            print(f"A task generated an exception: {e}")


# ==========================================
# 4. Show Final Results
# ==========================================
print("\n--- Final Database Contents ---")
print(duckdb_con.execute("SELECT * FROM my_inserts ORDER BY insert_time").df())
