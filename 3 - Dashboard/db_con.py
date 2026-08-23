import os
from pathlib import Path
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
def _is_running_in_docker():
    if os.path.exists('/.dockerenv'):
        return True

    cgroup_path = '/proc/1/cgroup'
    if os.path.exists(cgroup_path):
        try:
            with open(cgroup_path, 'r', encoding='utf-8') as f:
                cgroup_content = f.read()
            if 'docker' in cgroup_content or 'containerd' in cgroup_content:
                return True
        except OSError:
            pass

    return False


def get_db_params():
    base_dir = Path(__file__).resolve().parent.parent
    caminho_env = base_dir / '2 - Database' / 'db.env'
    load_dotenv(caminho_env, override=False)

    db_server = os.getenv('DB_SERVER')
    db_host = os.getenv('DB_HOST')

    if _is_running_in_docker():
        # In Docker Compose, prefer service discovery name (usually "db").
        server = db_host 
    else:
        # On localhost, prefer explicit local server first.
        server = 'localhost'

    database = os.getenv('DB_DATABASE', 'RAE2')  # database created by init_db.py
    username = os.getenv('DB_USER', 'sa')  # or 'adm111' if you prefer
    password = os.getenv('DB_PASSWORD')
    driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    return server, database, username, password, driver