# EIR Project - Relative Age Effect in Professional Football

This project analyzes the Relative Age Effect (RAE) in FIFA World Cup football using a step-by-step workflow: data collection, database modeling, dashboard visualization, and Docker deployment.


## Main Results

1. **Exploratory Data Analysis**
   - The percentage of players born in the first quarter of the year is highest (30.2%) among players who have participated in the most World Cup editions
   - Consistent with the literature, defender and goalkeeper are the positions with the highest RAE among players who have participated in at least four World Cup editions.
   - Using the Odds Ratio, the number of team compositions with significant RAE increases with the number of World Cup editions the team has played in. (e.g., Brazil has played in 22 editions and has 17 compositions with significant RAE)
2. **Binary Classification**
   - The class imbalance led to poor performance across the three algorithms trained despite the use of data augmentation techniques such as SMOTE.

## Project logical order

1. **Web Scraping**
   - Collect and organize data from 22 World Cups and more than 8000 players.
   - Main folder: `1 - Web Scrapping/`

2. **Database creation**
   - Transform CSV files into SQL Server tables (Relational Database).
   - Main build/load script: `2 - Database/2 - building database.py`
   - Environment configuration: `2 - Database/db.env`

3. **Dashboard**
   - Flask + Dash web app for indicators and visual analytics.
   - Main files: `3 - Dashboard/app.py`, `3 - Dashboard/dashboard.py`, `3 - Dashboard/db_con.py`

   ![Dashboard prototype](<3 - Dashboard/dashboard images/Dashboard-Prototype.png>)

4. **Dockerization**
   - Service orchestration (`db`, `db_init`, `app`) via Docker Compose.
   - Main file: `4 - Docker/docker-compose.yml`

5. **Additional analysis**
   - Exploratory analysis
   - Binary Classification (Logistic Regression, Random Forest, XGBoost)
   - Main folder: `5 - Data Analysis/`

## Dashboard

![First part Dashboard](<3 - Dashboard/dashboard images/First part dashboard.png>)

![Second part Dashboard](<3 - Dashboard/dashboard images/Second Part Dashboard.png>)

![Third part Dashboard](<3 - Dashboard/dashboard images/Third Part Dashboard.png>)

