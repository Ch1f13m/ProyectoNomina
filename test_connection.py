from db import get_connection

try:
    conn = get_connection()
    print("Conexión exitosa a SQL Server")
    cursor = conn.cursor()
    cursor.execute("SELECT GETDATE();")
    row = cursor.fetchone()
    print("Fecha y hora del servidor SQL:", row[0])
    conn.close()
except Exception as e:
    print("Error en la conexión:", e)
