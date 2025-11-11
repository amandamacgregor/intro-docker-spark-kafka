README  
# Practicing some DE tools  
Referencing: https://www.youtube.com/watch?v=PHsC_t0j1dU 
https://transparent-trout-f2f.notion.site/FreeCodeCamp-Data-Engineering-Course-Resources-e9d2b97aed5b4d4a922257d953c4e759
https://github.com/justinbchau/custom-elt-project

Docker, dbt, Airflow, Kafka (skipping airbyte and kafka portions)
Sprinkling of Python and SQL throughout

## Docker:
docker compose up
docker compose down
docker compose up --build (used this a lot)
docker exec -it elt_project_1-destination_postgres-1 psql -U postgres
To connect to db:
\c destination_db
To check if moving data around worked (so far):
\dt
It did! Can poke around through terminal using SQL at this point to see.
This means the batch script we've been building is working, even if it's not automated (which we might do later?)

## dbt:
installed the postgres plugin (had core, and snowflake plugin already from prior project)
nan ~/.dbt/profiles.yml
doublecheck the entries I put are correct

tests go into the model folder themselves (basics like not null, unique if PK)

docker compose up --build
Start containers in background (can still use terminal)
docker-compose up -d

View logs if you want to see what's happening
docker-compose logs -f

Stop watching logs (Ctrl+C just exits the logs, doesn't stop containers)
Ctrl+C here is safe!

When done, stop everything
docker-compose down - (the -v also kills the volumes)

to check the data:
docker exec -it elt_project_1-destination_postgres-1 psql -U postgres
\c destination_db
\dt
             List of relations
 Schema |     Name      | Type  |  Owner   
--------+---------------+-------+----------
 public | actors        | table | postgres
 public | film_actors   | table | postgres
 public | film_category | table | postgres
 public | film_ratings  | table | postgres
 public | films         | table | postgres
 public | users         | table | postgres
(6 rows)

docker-compose run dbt

Running into issues where I need way more and more complicated commands for docker to run in sequence
Adjusting conditions in the docker-compose file to see if it helps
(it did)
so, using docker compose down -v
the docker compose up
don't need run, getting specific, etc.

## airflow
Creating new folders and files - everything will be run from airflow.
Meaning, we're spinning up docker FROM airflow.
A lot of hyper-specific things commands added to the elt_dag.py file; not super focused on these right now. Plenty to trace back to really understand how the different mapping, root, etc is getting called across dbt, docker, airflow when it matters more than the general flow / getting it to work.

docker compose up now immediately runs init airflow
almost worked first try - a couple things to debug that seem related to version changes
webserver:
  command: airflow webserver

->

webserver:
  command: airflow api-server


[webserver]
secret_key = your_secret_key
```
->

[api]
secret_key = your_secret_key

Needed to add the same kind of conditions to say wait until init is complete before continuing as earlier in the project. Tutorial was just saying 'make sure these things have started', which has repeatedly been an issue for me.

Also had to create users via environment, not the command bash like the initial thought was.

docker compose up init-airflow -d
docker compose up
http://localhost:8080/

Can't log in, going back to bash version of command and user creation, pinning apache/airflow:2.10.2 instead of latest since that seems to be the root of the issue.

Had to open from an incognito window, but was able to log in finally.

Had file path issues, got a little ugly but got some code to work and the task finally passed.

dbt_run task now failing:
dbt can’t find the project
DockerOperator is trying to mount a temp dir that doesn’t exist on macOS (whaa..?)