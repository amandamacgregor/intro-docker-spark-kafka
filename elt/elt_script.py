import subprocess
import time
import os

def wait_for_postgres(host, max_retries=5, delay_seconds=5):
    # waiting for PostgreSQL to be available
    retries = 0
    while retries < max_retries:
        try:
            result = subprocess.run(
                ["pg_isready", "-h", host], check=True, capture_output=True, text=True)
            if "accepting connections" in result.stdout:
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

# Configuration for the source PostgreSQL database
source_config = {
    'dbname': 'source_db',
    'user': 'postgres',
    'password': 'secret',
    # Use the service name from docker-compose as the hostname
    'host': 'source_postgres'
}

# Configuration for the destination PostgreSQL database
destination_config = {
    'dbname': 'destination_db',
    'user': 'postgres',
    'password': 'secret',
    # Use the service name from docker-compose as the hostname
    'host': 'destination_postgres'
}

# Use pg_dump to dump the source database to a SQL file
dump_command = [
    'pg_dump',
    '-h', source_config['host'],
    '-U', source_config['user'],
    '-d', source_config['dbname'],
    '-f', 'data_dump.sql',
    '-w'  # Do not prompt for password
]

# Copy environment and add PGPASSWORD
# dict(PGPASSWORD=source_config['password']) creates a brand new environment with only one variable
# os.environ.copy() copies current environment and then add PGPASSWORD to it
# This way pg_dump gets all the system environment variables it needs (PATH to find libraries, locale settings, etc.) PLUS your password.
subprocess_env = os.environ.copy()
subprocess_env['PGPASSWORD'] = source_config['password']
# Set the PGPASSWORD environment variable to avoid password prompt
# subprocess_env = dict(PGPASSWORD=source_config['password']) ----this didn't work, new code is aboce

# Execute the dump command with error output
try:
    subprocess.run(dump_command, env=subprocess_env, check=True, capture_output=True, text=True)
except subprocess.CalledProcessError as e:
    print(f"pg_dump failed with error: {e.stderr}")
    exit(1)

# all that was to set up source. to get everything from source over to destination:
if not wait_for_postgres(host="destination_postgres"):
    exit(1)

load_command = [
    'psql',
    '-h', destination_config['host'],
    '-U', destination_config['user'],
    '-d', destination_config['dbname'],
    '-a', '-f', 'data_dump.sql',
]

subprocess_env = os.environ.copy()
subprocess_env['PGPASSWORD'] = destination_config['password']
# subprocess_env = dict(PGPASSWORD=destination_config['password']) ---this didn't work, new code is above

try:
    subprocess.run(load_command, env=subprocess_env, check=True, capture_output=True, text=True)
except subprocess.CalledProcessError as e:
    print(f"psql failed with error: {e.stderr}")
    exit(1)

print("Ending ELT Script.")