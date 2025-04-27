import pyodbc

def get_connection():
    server = '192.168.1.16'
    database = 'Nomina'
    username = 'Andres'
    password = '12345'

    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        f"TrustServerCertificate=yes;"
    )

    conn = pyodbc.connect(conn_str)
    return conn
