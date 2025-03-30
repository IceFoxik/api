import psycopg2
from contextlib import closing

# Настройка подключения к PostgreSQL
DATABASE_URL = "dbname=postgres user=postgres password=password host=localhost port=5432"

def get_db_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except psycopg2.OperationalError as e:
        print("Ошибка подключения к базе данных:", e)
        raise