import pyodbc
from config import DB_CONFIG

def get_db_connection():
    conn_str = (
        f"DRIVER={{{DB_CONFIG['driver']}}};"
        f"SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};"
        f"UID={DB_CONFIG['uid']};"
        f"PWD={DB_CONFIG['pwd']};"
        f"TrustServerCertificate={DB_CONFIG['TrustServerCertificate']};"
    )
    return pyodbc.connect(conn_str)