import os
import sys
import numpy as npa
import pandas as pd
from dotenv import load_dotenv
from pathlib import Path
from urllib.parse import quote_plus
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base
from werkzeug.security import generate_password_hash

# Resolve paths from this file location so Docker working_dir does not matter.
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

WEB_DIR_CANDIDATES = [
    PROJECT_ROOT / '1 - Web Scrapping',
    Path('/workspace/web-scrapping'),
]
web_scrapping_path = next((p for p in WEB_DIR_CANDIDATES if p.exists()), WEB_DIR_CANDIDATES[0])

def db_join(name):
    return str(SCRIPT_DIR / name)

def pjoin(name):
    return str(web_scrapping_path / name)

# Variáveis de ambiente lidas de db.env
env_path = db_join('db.env')
# Keep values already provided by the container (e.g. DB_SERVER=db in docker-compose).
load_dotenv(env_path, override=False)

DB_SERVER = os.getenv('DB_SERVER')
DB_NAME = os.getenv('DB_DATABASE')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
ODBC_DRIVER = os.getenv('DB_DRIVER')

# Lê arquivos auxiliares
with open(pjoin('name_of_all_worldcups.txt'), 'r', newline='') as f:    
    worldcups = f.read().splitlines(False)

with open(pjoin('name_of_all_teams.txt'), 'r', newline='') as f:
    name_of_all_teams = f.read().splitlines(False)

missing_vars = [name for name, value in {'DB_SERVER': DB_SERVER, 'DB_DATABASE': DB_NAME, 'DB_USER': DB_USER, 'DB_PASSWORD': DB_PASSWORD, 'DB_DRIVER': ODBC_DRIVER}.items() if not value]
if missing_vars:
    raise ValueError(f"Missing environment variables in db.env: {', '.join(missing_vars)}")

driver_q = quote_plus(ODBC_DRIVER)  # 'ODBC+Driver+18+for+SQL+Server'
base_params = f"driver={driver_q}&Encrypt=yes&TrustServerCertificate=yes"

def conn_str(database: str) -> str:
    return (
        f"mssql+pyodbc://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_SERVER}/{database}?"
        f"{base_params}"
    )

# 1) Connect to master and create DB if needed (must be AUTOCOMMIT)
engine_master = create_engine(conn_str("master"), fast_executemany=True)
with engine_master.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
    conn.execute(text(f"IF DB_ID('{DB_NAME}') IS NULL CREATE DATABASE [{DB_NAME}];"))
engine_master.dispose()

# 2) Now connect to your app DB
engine = create_engine(conn_str(DB_NAME), fast_executemany=True)
Base = declarative_base()

class Players_Table:
    def __init__(self, connection):
        self.conn = connection
    def create_players(self):
        self.conn.execute(text("""
            IF OBJECT_ID('dbo.TEAM_HAS_PLAYERS_TABLE','U') IS NOT NULL
                DROP TABLE dbo.TEAM_HAS_PLAYERS_TABLE;

            IF OBJECT_ID('dbo.PLAYERS_TABLE','U') IS NOT NULL
                DROP TABLE dbo.PLAYERS_TABLE;

            CREATE TABLE dbo.PLAYERS_TABLE(
                ID INT NOT NULL PRIMARY KEY,
                TEAM VARCHAR(55) NOT NULL,
                NAME VARCHAR(55) NOT NULL,
                BIRTH_DAY INT NOT NULL,
                BIRTH_MONTH INT NOT NULL,
                BIRTH_YEAR INT NOT NULL
            );
        """))
    def insert_values(self, id, team, players_name, day, month, year):
        # Evita quebra por aspas simples
        self.conn.execute(
            text("INSERT INTO dbo.PLAYERS_TABLE([ID],[TEAM],[NAME],[BIRTH_DAY],[BIRTH_MONTH],[BIRTH_YEAR]) VALUES (:id,:t,:n,:d,:m,:y)"),
            {"id": id, "t": team, "n": players_name, "d": day, "m": month, "y": year}
        )
    def insert_players(self):
        df = pd.read_csv(db_join('Players_table.csv'), sep=';')
        df.columns = df.columns.str.strip()

        required = {'ID', 'Team', 'Player', 'Day', 'Month', 'Year'}
        missing = required - set(df.columns)
        if missing:
            raise KeyError(f"Colunas ausentes no Players_table.csv: {sorted(missing)}")

        for _, row in df.iterrows():
            self.insert_values(
                int(row['ID']),
                str(row['Team']),
                str(row['Player']),
                int(row['Day']),
                int(row['Month']),
                int(row['Year'])
            )
    def delete_players(self):
        self.conn.execute(text("IF OBJECT_ID('dbo.PLAYERS_TABLE','U') IS NOT NULL DROP TABLE dbo.PLAYERS_TABLE;"))

class Team_has_Players_Table:
    def __init__(self, connection):
        self.conn = connection
    def create_table(self):
        self.conn.execute(text("""
            IF OBJECT_ID('dbo.TEAM_HAS_PLAYERS_TABLE','U') IS NOT NULL
                DROP TABLE dbo.TEAM_HAS_PLAYERS_TABLE;

            CREATE TABLE dbo.TEAM_HAS_PLAYERS_TABLE(
                PLAYERS_ID INT NOT NULL,
                GAME_YEAR INT NOT NULL,
                TEAMS_NAME VARCHAR(55) NOT NULL,
                POSITION VARCHAR(55) NOT NULL,
                CONSTRAINT FK_TEAM_HAS_PLAYERS_PLAYER
                    FOREIGN KEY (PLAYERS_ID) REFERENCES dbo.PLAYERS_TABLE(ID)
            );
        """))
    def insert_values(self, player_id, year_played, teams_name, position):
        self.conn.execute(
            text("INSERT INTO dbo.TEAM_HAS_PLAYERS_TABLE([PLAYERS_ID],[GAME_YEAR],[TEAMS_NAME],[POSITION]) VALUES (:pid,:y,:t,:p)"),
            {"pid": int(player_id), "y": int(year_played), "t": str(teams_name), "p": str(position)}
        )
    def get_player_id_by_name(self, player_name):
        return self.conn.execute(
            text("SELECT TOP 1 ID FROM dbo.PLAYERS_TABLE WHERE NAME = :n"),
            {"n": str(player_name)}
        ).scalar()
    def insert_all(self):
        df = pd.read_csv(db_join('Game_Table.csv'),index_col=0,sep = ';')
        for i in range(1, df.shape[0] + 1):
            player_name, year_played, teams_name, position, player_id = df.loc[i, ['Player', 'Game_Year', 'Team', 'Position', 'PLAYERS_ID']].values

            if pd.isna(player_id):
                player_id = self.get_player_id_by_name(player_name)

            if player_id is None or pd.isna(player_id):
                continue

            self.insert_values(player_id, year_played, teams_name, position)
    def delete_table(self):
        self.conn.execute(text("IF OBJECT_ID('dbo.TEAM_HAS_PLAYERS_TABLE','U') IS NOT NULL DROP TABLE dbo.TEAM_HAS_PLAYERS_TABLE;"))

class Teams_Table:
    def __init__(self, connection):
        self.conn = connection
    def create_table(self):
        self.conn.execute(text("""
            IF OBJECT_ID('dbo.TEAMS_TABLE','U') IS NULL
            CREATE TABLE dbo.TEAMS_TABLE(
                TEAM VARCHAR(55) NOT NULL
            );
        """))
    def insert_values(self, teams_name):
        self.conn.execute(
            text("INSERT INTO dbo.TEAMS_TABLE([TEAM]) VALUES (:t)"),
            {"t": teams_name}
        )
    def insert_all(self):
        for team in name_of_all_teams:
            self.insert_values(team)
    def delete_table(self):
        self.conn.execute(text("IF OBJECT_ID('dbo.TEAMS_TABLE','U') IS NOT NULL DROP TABLE dbo.TEAMS_TABLE;"))

class Wcup_has_Teams_Table:
    def __init__(self, connection):
        self.conn = connection
    def create_table(self):
        self.conn.execute(text("""
            IF OBJECT_ID('dbo.WCUP_HAS_TEAMS_TABLE','U') IS NULL
            CREATE TABLE dbo.WCUP_HAS_TEAMS_TABLE(
                YEAR INT NOT NULL,
                TEAM VARCHAR(55) NOT NULL,
                TYPE VARCHAR(55) NOT NULL,
                TOTAL FLOAT NOT NULL,
                FIRST_QUARTER FLOAT NOT NULL,
                SECOND_QUARTER FLOAT NOT NULL,
                THIRD_QUARTER FLOAT NOT NULL,
                FORTH_QUARTER FLOAT NOT NULL
            );
        """))
    def insert_values(self, wcup_year, team, TYPE, total, first_quarter, second_quarter, third_quarter, forth_quarter):
        self.conn.execute(
            text("""INSERT INTO dbo.WCUP_HAS_TEAMS_TABLE
                    ([YEAR],[TEAM],[TYPE],[TOTAL],[FIRST_QUARTER],[SECOND_QUARTER],[THIRD_QUARTER],[FORTH_QUARTER])
                    VALUES (:y,:team,:typ,:tot,:q1,:q2,:q3,:q4)"""),
            {"y": int(wcup_year), "team": team, "typ": TYPE, "tot": float(total),
             "q1": float(first_quarter), "q2": float(second_quarter),
             "q3": float(third_quarter), "q4": float(forth_quarter)}
        )
    def insert_wcup_has_teams(self):
        df = pd.read_csv(db_join('wcup_has_teams.csv'), encoding='utf-8-sig')
        for worldcup in worldcups:
            wcup_year = int(worldcup.split(' ')[0])
            year_wcup = df[df['YEAR'] == wcup_year]  # já filtrado pelo ano
            for team in year_wcup['TEAM'].unique():
                team_wcup = year_wcup[year_wcup['TEAM'] == team]  # filtrado pelo time
                for TYPE in ['Frequence', 'Percentage(%)']:
                    type_wcup = team_wcup[team_wcup['TYPE'] == TYPE]  # filtrado pelo tipo
                    if not type_wcup.empty:
                        row = type_wcup.iloc[0]
                        self.insert_values(
                            wcup_year,
                            team,
                            TYPE,
                            row['N_PLAYERS'],
                            row['FIRST_QUARTILE'],
                            row['SECOND_QUARTILE'],
                            row['THIRD_QUARTILE'],
                            row['FORTH_QUARTILE']
                        )
    def delete_wcup(self):
        self.conn.execute(text("IF OBJECT_ID('dbo.WCUP_HAS_TEAMS_TABLE','U') IS NOT NULL DROP TABLE dbo.WCUP_HAS_TEAMS_TABLE;"))

class Wcup:
    def __init__(self, connection):
        self.conn = connection
    def create_table(self):
        self.conn.execute(text("""
            IF OBJECT_ID('dbo.WORLDCUP_TABLE','U') IS NULL
            CREATE TABLE dbo.WORLDCUP_TABLE(
                GAME_YEAR INT NOT NULL,
                HOST VARCHAR(55) NOT NULL,
                TYPE VARCHAR(55) NOT NULL,
                N_PLAYERS FLOAT NOT NULL,
                FIRST_QUARTER FLOAT NOT NULL,
                SECOND_QUARTER FLOAT NOT NULL,
                THIRD_QUARTER FLOAT NOT NULL,
                FORTH_QUARTER FLOAT NOT NULL
            );
        """))
    def insert_values(self, game_year, host, TYPE, N_PLAYERS, FIRST_QUARTER, SECOND_QUARTER, THIRD_QUARTER, FORTH_QUARTER):
        self.conn.execute(
            text("""INSERT INTO dbo.WORLDCUP_TABLE
                    ([GAME_YEAR],[HOST],[TYPE],[N_PLAYERS],[FIRST_QUARTER],[SECOND_QUARTER],[THIRD_QUARTER],[FORTH_QUARTER])
                    VALUES (:y,:h,:t,:n,:q1,:q2,:q3,:q4)"""),
            {"y": int(game_year), "h": host, "t": TYPE, "n": float(N_PLAYERS),
             "q1": float(FIRST_QUARTER), "q2": float(SECOND_QUARTER),
             "q3": float(THIRD_QUARTER), "q4": float(FORTH_QUARTER)}
        )
    def insert_wcup(self):
        df = pd.read_csv(db_join('Worldcup_Quarters.csv'), index_col=0)
        df.index = range(1, df.shape[0] + 1)
        for i in range(1, df.shape[0] + 1):
            GAME_YEAR, HOST, TYPE, N_PLAYERS, FIRST_QUARTER, SECOND_QUARTER, THIRD_QUARTER, FORTH_QUARTER = df.loc[i].values
            self.insert_values(GAME_YEAR, HOST, TYPE, N_PLAYERS, FIRST_QUARTER, SECOND_QUARTER, THIRD_QUARTER, FORTH_QUARTER)
    def delete_wcup(self):
        self.conn.execute(text("IF OBJECT_ID('dbo.WORLDCUP_TABLE','U') IS NOT NULL DROP TABLE dbo.WORLDCUP_TABLE;"))

class Users_Table:
    def __init__(self, connection):
        self.conn = connection
    def create_users_table(self):
        try:
            self.conn.execute(text("""
                IF OBJECT_ID('dbo.USERS_TABLE','U') IS NULL
                CREATE TABLE dbo.USERS_TABLE (
                    id INT PRIMARY KEY IDENTITY(1,1),
                    nome VARCHAR(100) NOT NULL,
                    email VARCHAR(150) NOT NULL UNIQUE,
                    senha VARCHAR(255) NOT NULL,
                    data_nascimento DATE NULL,
                    telefone VARCHAR(20) NULL,
                    criado_em DATETIME DEFAULT GETDATE()
                );
            """))
            print("Tabela 'USERS_TABLE' criada (ou já existia).")
        except Exception as e:
            print(f"Erro ao criar tabela 'USERS_TABLE': {e}")
    def insert_admin(self, nome, email, senha):
        senha_hash = generate_password_hash(senha)
        try:
            self.conn.execute(
                text("""
                    IF NOT EXISTS (SELECT 1 FROM dbo.USERS_TABLE WHERE email = :e)
                        INSERT INTO dbo.USERS_TABLE (nome, email, senha) VALUES (:n, :e, :s)
                """),
                {"n": nome, "e": email, "s": senha_hash}
            )
            print("Usuário admin inserido com sucesso.")
        except Exception as e:
            print(f"Erro ao inserir usuário admin: {e}")

# Execução principal
try:
    with engine.begin() as connection:
        try:
            players = Players_Table(connection)
            players.create_players()
            players.insert_players()
            print("PLAYERS_TABLE criada e populada.")
        except Exception as e:
            print(f"Erro em PLAYERS_TABLE: {e}")

        try:
            obj = Team_has_Players_Table(connection)
            obj.create_table()
            obj.insert_all()
            print("TEAM_HAS_PLAYERS_TABLE criada e populada.")
        except Exception as e:
            print(f"Erro em TEAM_HAS_PLAYERS_TABLE: {e}")

        try:
            team = Teams_Table(connection)
            team.create_table()
            team.insert_all()
            print("TEAMS_TABLE criada e populada.")
        except Exception as e:
            print(f"Erro em TEAMS_TABLE: {e}")

        try:
            Wcup_has_Teams_obj = Wcup_has_Teams_Table(connection)
            Wcup_has_Teams_obj.create_table()
            Wcup_has_Teams_obj.insert_wcup_has_teams()
            print("WCUP_HAS_TEAMS_TABLE criada e populada.")
        except Exception as e:
            print(f"Erro em WCUP_HAS_TEAMS_TABLE: {e}")

        try:
            Wcup_obj = Wcup(connection)
            Wcup_obj.create_table()
            Wcup_obj.insert_wcup()
            print("WORLDCUP_TABLE criada e populada.")
        except Exception as e:
            print(f"Erro em WORLDCUP_TABLE: {e}")

        try:
            users = Users_Table(connection)
            users.create_users_table()
            users.insert_admin("admin", "EIR@ufma.com.br","admin")
            print("USERS_TABLE criada.")
        except Exception as e:
            print(f"Erro em USERS_TABLE: {e}")

except Exception as e:
    print(f"Erro geral: {e}")
    sys.exit(1)
finally:
    engine.dispose()