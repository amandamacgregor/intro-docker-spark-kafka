README  
Practicing some tools  
Referencing: https://www.youtube.com/watch?v=PHsC_t0j1dU  
Docker, dbt, Airflow, Kafka  
Sprinkling of Python and SQL throughout

Docker:
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

dbt:
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