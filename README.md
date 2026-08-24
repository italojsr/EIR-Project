# EIR Project - Relative Age Effect in Football

This project analyzes the Relative Age Effect (RAE) in FIFA World Cup football using a step-by-step workflow: data collection, database modeling, dashboard visualization, and Docker deployment.

## Project logical order

1. **Web Scraping**
   - Collect and organize base data for World Cups and players.
   - Main folder: `1 - Web Scrapping/`

2. **Database creation**
   - Transform CSV files into SQL Server tables.
   - Main build/load script: `2 - Database/2 - building database.py`
   - Environment configuration: `2 - Database/db.env`

3. **Dashboard**
   - Flask + Dash web app for indicators and visual analytics.
   - Main files: `3 - Dashboard/app.py`, `3 - Dashboard/dashboard.py`, `3 - Dashboard/db_con.py`

4. **Dockerization**
   - Service orchestration (`db`, `db_init`, `app`) via Docker Compose.
   - Main file: `4 - Docker/docker-compose.yml`

5. **Additional analysis**
   - Extra notebooks and exploratory analysis.
   - Main folder: `5 - Data Analysis/`

---

## Folder structure summary

- `1 - Web Scrapping/` - initial data collection and preparation
- `2 - Database/` - scripts and files for DB creation/population
- `3 - Dashboard/` - Flask/Dash application
- `4 - Docker/` - compose and container infrastructure
- `5 - Data Analysis/` - analysis notebooks

---

## Requirements

- Python 3.11+
- Docker and Docker Compose
- SQL Server (for non-Docker/local execution)
- ODBC Driver 17 for SQL Server

---

## Environment variables

Database settings are stored in `2 - Database/db.env`.

Example keys used in this project:

- `DB_SERVER`
- `DB_DATABASE`
- `DB_USER`
- `DB_PASSWORD`
- `DB_DRIVER`

> `db.env` is listed in `.gitignore` and should never be published.

---

## Run with Docker (recommended workflow)

From the repository root:

1. Update `2 - Database/db.env` with your values.
2. Start services using the compose file in `4 - Docker`:

```bash
docker compose -f "4 - Docker/docker-compose.yml" up --build
```

Expected services:

- `db`: SQL Server
- `db_init`: creates and populates tables
- `app`: starts the dashboard

Dashboard URL:

- `http://localhost:935`

---

## Run locally (without Docker)

1. Configure local SQL Server.
2. Update `2 - Database/db.env` for local settings.
3. Run the database build/population script:

```bash
python "2 - Database/2 - building database.py"
```

4. Run the dashboard app:

```bash
python "3 - Dashboard/app.py"
```

---

## Notes
- After changing Docker environment variables, recreate containers so changes are applied.
