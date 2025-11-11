README  
# Building another ELT Pipeline 
### (The Accessible Way - coding along and taking 10x longer than the video while I debug my own issues and learn as I go)
Referencing: https://www.youtube.com/watch?v=PHsC_t0j1dU 
https://transparent-trout-f2f.notion.site/FreeCodeCamp-Data-Engineering-Course-Resources-e9d2b97aed5b4d4a922257d953c4e759
https://github.com/justinbchau/custom-elt-project

Docker, dbt, Airflow, Kafka (skipping airbyte and kafka portions)
Sprinkling of Python and SQL throughout

A hands-on data engineering project where I got into Docker, dbt, Airflow, and PostgreSQL. I built this while following a tutorial (a 2 hour video), hit a bunch of real-world issues, and learned a ton debugging my way through them (took me 10 hours total.)

This was super simple! Basic CTEs, nothing crazy as far as tests, nothing crazy as far as data sources (would like to play with something like grabbing API data next), super contrived to think something like films and actors would need to load on a certain schedule, no real desire to think through what tables would need to be loaded regularly, with what frequency, for analysts to make use of this. Unclear, for example, if there would be a need to think through change data capture, incremental loading, etc.

**High Level** Extract data from one database, load it into another, transform it with dbt, orchestrate it all with Airflow.

## Revisiting what I did

- [The Big Picture](#the-big-picture)
- [How It Actually Works](#how-it-actually-works)
- [The Tech Stack](#the-tech-stack)
- [The Data Model](#the-data-model)
- [Running It Yourself](#running-it-yourself)
- [Things I Learned (The Hard Way)](#things-i-learned-the-hard-way)
- [What I'd Build Next](#what-id-build-next)

---

## The Big Picture

Here's what we're working with:

```
Source DB (PostgreSQL)
    ↓
Python ELT Script (pg_dump → psql)
    ↓
Destination DB (PostgreSQL)
    ↓
dbt (transforms the data)
    ↓
Analytics-ready tables

All orchestrated by Airflow (this was just lightweight practice, I have a lot more to learn)
```

**Why this matters:** This is basically how most companies move data around (with varying tools and maturity). Source system → data warehouse → analytics. I wanted to practice building from scratch using open source tools.

### The Components

**Source Database** - basic 'dummy' production database with film data (movies, actors, ratings). Initialized with a SQL script (init.sql) so there's data to work with. Used postgres here.

**ELT Script** - Python script that waits for the database to be ready (with retries because databases are slow), dumps all the data, and loads it into the destination. Used `pg_dump` and `psql` because those seem like standards.

**Destination Database** - The data warehouse. This is where the raw data lands and where dbt works its magic. Used postgres here as well.

**dbt** - Transforms raw data into useful stuff. "I want to see films with their actors and categorize them by rating" kind of thing. That's what dbt does with SQL.

**Airflow** - The conductor. Makes sure everything runs in the right order, on schedule, and gives you a UI to see what's happening (or what broke). Used postgres again for logging the tasks. Honestly, I have a lot more to learn and this seemed like too simple of a case to get much from this tool. And it took the longest to debug and get up and running!

---

## How It Actually Works

### The Flow

1. **Airflow kicks off** → Checks if source database is alive
2. **ELT script runs** → Dumps source data, loads into destination
3. **dbt transformation** → Takes raw tables, creates analytical models
4. **Done!** → You've got clean data ready for dashboards/analysis

### The Airflow DAG

```
check_source_db 
    ↓
run_elt_script 
    ↓
run_dbt_models
    ↓
hopefully successful
```

Each arrow is a dependency. If one fails, the next one doesn't run. This is way better than just hoping things run in order.

---

## The Tech Stack

| What | Why I Used It |
|------|---------------|
| **Docker** | Because "works on my machine" isn't good enough / because this has rapidly turned into an industry standard |
| **PostgreSQL 15** | Industry standard, and it's pretty familiar |
| **Python 3.8** | For the ELT script. Could've used bash but Python felt cleaner - and python is a more marketable skill for what I want to do |
| **dbt 1.4.7** | SQL-based transformations. Again, industry standard. Played with some jinjas as well, more to explore there |
| **Airflow 2.10.2** | Orchestration. Had to downgrade from 3.x because of breaking changes - this was a lot of time! The version changes even though the tutorial wasn't that old, coupled with path naming issues that I had to chase through the layers.. a lot of exposure, but man this added up |

**Version pinning is important!** Learned this when I spent 2 hours debugging why Airflow 3.x commands didn't work. Q: in real world projects, are versions pinned? They must be, right?

### Architecture Overview
```
┌─────────────────────────────────────────────────────────────────────┐
│                         AIRFLOW ORCHESTRATION                        │
│                    (Scheduling & Dependency Management)              │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────┐
│  SOURCE DATABASE │  │   ELT SCRIPT     │  │ DESTINATION DATABASE│
│   (PostgreSQL)   │─▶│   (Python +      │─▶│    (PostgreSQL)     │
│                  │  │   pg_dump/psql)  │  │                     │
│  • Raw film data │  │                  │  │  • Loaded raw data  │
│  • User data     │  │  Batch data      │  │  • dbt models       │
│  • Actor data    │  │  transfer        │  │  • Transformed data │
└──────────────────┘  └──────────────────┘  └──────────┬──────────┘
                                                       │
                                                       ▼
                                            ┌───────────────────────┐
                                            │   DBT TRANSFORMATIONS │
                                            │                       │
                                            │  • Data modeling      │
                                            │  • Business logic     │
                                            │  • Quality tests      │
                                            └───────────────────────┘
```

---

## The Data Model

### What We Start With
Via the table creation and inserting data in init.sql:

```
films table:
- film_id, title, release_date, price, rating, user_rating

actors table:
- actor_id, actor_name

film_actors table (the many-to-many junction):
- film_id, actor_id
```
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   films     │     │ film_actors  │     │   actors    │
├─────────────┤     ├──────────────┤     ├─────────────┤
│ film_id (PK)│────▶│ film_id (FK) │◀────│ actor_id(PK)│
│ title       │     │ actor_id(FK) │     │ actor_name  │
│ release_date│     └──────────────┘     └─────────────┘
│ price       │
│ rating      │
│ user_rating │
└─────────────┘
```
Pretty standard database stuff.

### What We Build

The `film_ratings` model combines everything into one analytics-ready table:

```sql
-- Step 1: Add business logic
WITH films_with_ratings AS (
    SELECT
        *,
        CASE
            WHEN user_rating >= 4.5 THEN 'Excellent'
            WHEN user_rating >= 4.0 THEN 'Good'
            WHEN user_rating >= 3.0 THEN 'Average'
            ELSE 'Poor'
        END as rating_category
    FROM {{ ref('films') }}
),

-- Step 2: Aggregate actors (this seemed wholly unneccesary and I lost the plot of doing things like the string agg; there was only one actor per film in the source data! Oh well, there's going to be contrived stuff in projects like this to keep them accessible.)
films_with_actors AS (
    SELECT
        f.film_id,
        f.title,
        STRING_AGG(DISTINCT a.actor_name, ', ') AS actors
    FROM {{ ref('films') }} f
    LEFT JOIN {{ ref('film_actors') }} fa ON f.film_id = fa.film_id
    LEFT JOIN {{ ref('actors') }} a ON fa.actor_id = a.actor_id
    GROUP BY f.film_id, f.title
)

-- Step 3: Put it all together
SELECT 
    fwr.*,
    fwa.actors
FROM films_with_ratings fwr 
LEFT JOIN films_with_actors fwa ON fwr.film_id = fwa.film_id
```

**Why CTEs?** Because jamming all this logic into one massive query is a nightmare to debug - at least at scale. So keeping bes practices in place even with small projects like this helps build muscle memory. CTEs let you build in stages, test each piece, and actually understand what's happening. BUT also, they're industry standard and a lot of pipelines use them - things just run better with them.

At one point when checking my tables, I was getting "Leonardo DiCaprio" repeated 27 times. Fun times debugging that one (I wasn't removing volumes every time I docker compose down)

### The Macro

I wrapped this in a dbt macro called `generate_film_ratings()` to make it reusable. BUT - dbt can't figure out dependencies when `ref()` is inside a macro, so you have to add hints:

```sql
-- depends_on: {{ ref('films') }}
-- depends_on: {{ ref('film_actors') }}
-- depends_on: {{ ref('actors') }}

{{ generate_film_ratings() }}
```

Learned this the hard way when dbt kept complaining it couldn't find dependencies - but I want to look into this more, since the tutorial didn't have any of these issues, and also didn't need to add these 'hints'.

---

## Running It Yourself

### You'll Need
- Docker Desktop
- 8GB+ RAM
- Ports 5433, 5434, 8080 available

### The Commands

```bash
# Start everything
docker-compose up -d

# Access Airflow
open http://localhost:8080
# Login: airflow / password

# Nuclear option (stops everything, and deletes all data)
docker-compose down -v
```

### Debugging Commands I Used A LOT

```bash
# Check destination database
docker exec -it elt_project_1-destination_postgres-1 psql -U postgres

# Inside psql:
\c destination_db  # Connect to the database
\dt               # List tables
select * from users; # Checked why I couldn't log into airflow at first
select * from films_with_ratings; #see what the CTE produced, before and after using macros
\q                # Quit

# Rebuild everything (when you change code)
docker-compose up --build
```

---

## Things I Learned (The Hard Way)

### 1. Docker Dependencies Are Trickier Than You Think

**The Problem:** `depends_on` just waits for containers to START, not for them to be READY. So my ELT script would run before PostgreSQL was actually accepting connections.

**The Fix:** Added retry logic with `pg_isready` in the Python script. Also used `condition: service_completed_successfully` in docker-compose to wait for tasks to actually finish.

**The Lesson:** Always assume services take time to initialize. Build in retry logic. The tutorial had plenty of code for this but it all stopped at 'make sure those things have started'. I needed them to be done before moving on.

### 2. Version Hell Is Real

**The Problem:** My pg_dump (v15) didn't work with PostgreSQL 18. Tutorial used Airflow 2.x, I started with 3.x and nothing worked.

**The Fix:** Pinned everything to version 15 for PostgreSQL, downgraded Airflow to 2.10.2.

**The Lesson:** Pin. Your. Versions. Especially in tutorials that are more than 6 months old. This is wild to me, because my naive brain is like 'just put :latest everywhere and you won't have issues! BUT - everything changes. The most basic of commands or lines of codes will deprecate.

### 3. Environment Variables Are Explicit

**The Problem:** My pg_dump kept failing with password errors even though I set `PGPASSWORD`.

**The Fix:** Changed from `dict(PGPASSWORD=password)` to `os.environ.copy()` then adding the password. The first approach nukes all other env variables.

**The Lesson:** Subprocesses don't inherit environment automatically. You have to explicitly pass it.

### 4. dbt Macros Break Dependency Detection

**The Problem:** When I moved my SQL into a macro, dbt couldn't figure out which models depended on what.

**The Fix:** Added dependency comments at the top of the file:
```sql
-- depends_on: {{ ref('films') }}
```

**The Lesson:** Macros are evaluated after dependency resolution. Be explicit. Be open to a fix like this (I resisted, even checked the tutorial code to confirm this wasn't done in there), but this ended up working for me and made enough sense that I ran with it.

### 5. macOS Docker Has Weird Path Issues

**The Problem:** Airflow couldn't find my dbt project directory. Paths that worked on the tutorial's Linux setup didn't work on my Mac.

**The Fix:** Lots of path debugging. Eventually got the right combination of Docker volume mounts.

**The Lesson:** Cross-platform Docker can be painful. Document your paths clearly. This was really good exposure but won't be the last time I have to run through this, I'm sure.

---

## What I'd Build Next

### Quick-ish improvements

**Data Quality Tests**
Add dbt tests for:
- Not null checks on important fields
- Unique constraints on IDs
- Relationship validation (every film_actor points to real film & actor)
- Custom tests for business rules (e.g., ratings are 0-5)

**Better Monitoring**
- Airflow email alerts when things fail
- Slack notifications for pipeline status
- Track how long each step takes

**Incremental Models**
Right now dbt rebuilds everything every time. For bigger datasets, I'd use incremental models to only process new/changed data.

**CI/CD**
- Automated deployment when merging to main

### More Ambitious

**Add Streaming**
Kafka + Spark Structured Streaming for real-time data. Batch is fine for learning but streaming is where it gets interesting. This tutorial was meant to go through Kaftka but I want to bail onto other things.

**Cloud Migration**
Deploy to AWS:
- RDS for databases
- Management for Airflow
- S3 for data lake
- Terraform to manage it all

**Data Lake Architecture**
Implement medallion (bronze/silver/gold) - I've just started to read about this, could be juicy:
- Bronze: Raw data as-is
- Silver: Cleaned & validated
- Gold: Business-level aggregations

### Long Term (If This Were Real)

**Production Features**
- Cost monitoring per pipeline
- Auto-scaling based on load
- Multi-region failover

**ML Integration**
Doubtful for this project - feels really convtrived on this data but who knows.
- Feature store for ML models
- Real-time prediction pipelines
- Model training orchestration
- A/B testing infrastructure

**Data Governance**
Always good to practice.
- PII detection & masking
- RBAC for data access
- Audit logging
- Data catalog (so people can actually find stuff)

---

## Project Structure

```
intro-docker-spark-kafka/
├── docker-compose.yaml          # The main config file. 
├── Dockerfile                   # Airflow container setup
├── airflow/
│   └── dags/
│       └── elt_dag.py          # Pipeline definition
├── elt_script/
│   ├── Dockerfile              # Python + pg tools
│   └── elt_script.py           # Extract & Load logic
├── postgres_transformations/    # dbt project
│   ├── models/
│   │   └── example/
│   │       ├── film_ratings.sql
│   │       ├── films.sql
│   │       └── [other models]
│   └── macros/
│       └── film_ratings_macro.sql
└── source_db_init/
    └── init.sql                # Sample data
```

---

## Resources That Helped

- [Justin Chau's Tutorial](https://www.youtube.com/watch?v=PHsC_t0j1dU) - The original inspiration
- [FreeCodeCamp Course](https://transparent-trout-f2f.notion.site/FreeCodeCamp-Data-Engineering-Course-Resources-e9d2b97aed5b4d4a922257d953c4e759) - More context
- [Tutorial Repo](https://github.com/justinbchau/custom-elt-project) - Reference implementation
- Stack Overflow - ..obviously
- Claude AI - For debugging weird Docker issues and explaining dbt concepts, helping to summarize learnings

---

## Final Thoughts

This project taught me way more than just "how to set up Airflow." The real learning came from:
- Debugging version conflicts
- Understanding Docker networking
- Figuring out why my environment variables weren't passing through
- Learning when to use macros vs. models in dbt
- Realizing that tutorials always hide the messy parts

If you're learning data engineering, build something like this. Not because the code is complex (it's not), but because you'll hit all the real-world issues that tutorials skip over.

---


### Notes from working through the project..
This repository contains a custom Extract, Load, Transform (ELT) project that utilizes Docker and PostgreSQL to demonstrate a simple ELT process.

Repository Structure
docker-compose.yaml: This file contains the configuration for Docker Compose, which is used to orchestrate multiple Docker containers. It defines three services:

source_postgres: The source PostgreSQL database.
destination_postgres: The destination PostgreSQL database.
elt_script: The service that runs the ELT script.
elt_script/Dockerfile: This Dockerfile sets up a Python environment and installs the PostgreSQL client. It also copies the ELT script into the container and sets it as the default command.

elt_script/elt_script.py: This Python script performs the ELT process. It waits for the source PostgreSQL database to become available, then dumps its data to a SQL file and loads this data into the destination PostgreSQL database.

source_db_init/init.sql: This SQL script initializes the source database with sample data. It creates tables for users, films, film categories, actors, and film actors, and inserts sample data into these tables.

How It Works
Docker Compose: Using the docker-compose.yaml file, three Docker containers are spun up:

A source PostgreSQL database with sample data.
A destination PostgreSQL database.
A Python environment that runs the ELT script.
ELT Process: The elt_script.py waits for the source PostgreSQL database to become available. Once it's available, the script uses pg_dump to dump the source database to a SQL file. Then, it uses psql to load this SQL file into the destination PostgreSQL database.

Database Initialization: The init.sql script initializes the source database with sample data. It creates several tables and populates them with sample data.

CRON Job Implementation
In this branch, a CRON job has been implemented to automate the ELT process. The CRON job is scheduled to run the ELT script at specified intervals, ensuring that the data in the destination PostgreSQL database is regularly updated with the latest data from the source database.

To configure the CRON job:

Currently, the CRON job is setup to run every day at 3am.
You can adjust the time as needed within the Dockerfile found in the elt_script folder.
Getting Started
Ensure you have Docker and Docker Compose installed on your machine.
Clone this repository.
Navigate to the repository directory and run docker-compose up.
Once all containers are up and running, the ELT process will start automatically.
After the ELT process completes, you can access the source and destination PostgreSQL databases on ports 5433 and 5434, respectively.

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
^this ended up being more path issues. Resolved, all tasks passed within the dag.