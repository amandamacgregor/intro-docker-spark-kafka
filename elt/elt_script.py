import subprocess
import time

def wait_for_postgres(host, max_retries=5, delay_seconds=5):
    # waiting for PostgreSQL to be available
    retries = 0
    while retries < max_retries:
        try:
            result = subprocess.run(
                ["pg_isready", "-h", host], check=True, capture_output=True, text=True)
            if "accepting conenctions" in result.stdout:
                print ("Successfully connected to Postgres")
                return True
        except subprocess.CalledProcessError as e:
            print(f"Error connecting to Postgres: {e}")
            retries += 1
            print(
                f"Retrying in {delay_seconds} seconds... (Attempt {retries}/{max_retries})")
            time.sleep(delay_seconds)
        print("Max retries reached. Exiting")
        return False


if not wait_for_postgres(host="source_postgres"):
    exit(1)

print("Starting ELT Script")

source_config = {
    'dbname': 'source_db',
    'user': 'postgres',
    'password': 'secret',
    'host': 'source_postgres'
}

destination_config = {
    'dbname': 'destination_db',
    'user': 'postgres',
    'password': 'secret',
    'host': 'destination_db'
}

dump_command = [
    'pg_dump',
    '-h', 
]
