from datetime import datetime, timedelta
from airflow import DAG
from docker.types import Mount
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.docker.operators.docker import DockerOperator
import subprocess

# arguments airflow needs to do it's thing
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
}

# tell airflow where to look for the script, then run it, with a quick error check
def run_elt_script():
    script_path = "/opt/airflow/elt_script/elt_script.py"
    result = subprocess.run(["python", script_path],
                            capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Script failed with error: {result.stderr}")
    else:
        print(result.stdout)

# default args, description, start time - basics
dag = DAG(
    'elt_and_dbt',
    default_args=default_args,
    description='An ELT workflow with dbt',
    start_date=datetime(2025, 11,11),
    catchup=False,
)

# point to and run the right thing
t1 = PythonOperator(
    task_id='run_elt_script',
    python_callable=run_elt_script,
    dag=dag,
)

# the good stuff - airflow will create dbt in a new docker container, running and mounting everything we need to run dbt on top of the destination
t2 = DockerOperator(
    task_id='dbt_run',
    image='ghcr.io/dbt-labs/dbt-postgres:1.4.7',
    command=[
        "run",
        "--profiles-dir",
        "/root",
        "--project-dir",
        "/dbt",
        "--full-refresh"
    ],
    auto_remove=True,
    docker_url="unix://var/run/docker.sock",
    network_mode="bridge",
    mounts=[
        Mount(source='/Users/amandamacgregor/Documents/DE_SkillRefresh/elt_project_1',
              target='/dbt', type='bind'),
        Mount(source='/Users/amandamacgregor/.dbt', target='/root', type='bind'),
    ],
    dag=dag
)

# creating the order we want them to run
t1 >> t2