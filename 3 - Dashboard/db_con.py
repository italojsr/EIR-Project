import os
from urllib.parse import quote_plus
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from dotenv import load_dotenv


def database_connection(server, database, username, password, driver):
    # URL encode the driver and password to handle special characters
    driver_encoded = quote_plus(driver)
    password_encoded = quote_plus(password)
    
    # SQLAlchemy connection string for SQL Server with encryption params
    connection_string = f'mssql+pyodbc://{username}:{password_encoded}@{server}/{database}?driver={driver_encoded}&Encrypt=yes&TrustServerCertificate=yes'
    
    # Create SQLAlchemy engine
    engine = create_engine(connection_string, pool_pre_ping=True, fast_executemany=True)
    return engine

# Get connection parameters from environment variables (Docker-friendly)
def get_db_params():
    caminho_env = '../2 - Database/db.env'
    load_dotenv(caminho_env)
    server =  os.getenv('DB_SERVER') or os.getenv('DB_HOST') or 'localhost'  # 'db' is the service name in docker-compose
    database = os.getenv('DB_DATABASE', 'RAE2')  # database created by init_db.py
    username = os.getenv('DB_USER', 'sa')  # or 'adm111' if you prefer
    password = os.getenv('DB_PASSWORD')
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    return server, database, username, password, driver