from pymongo import MongoClient

DB_CONFIG = {
    'driver': 'ODBC Driver 18 for SQL Server',
    'server': '192.168.1.13',
    'database': 'Nomina',
    'uid': 'Andres',
    'pwd': '12345',
    'TrustServerCertificate': 'yes'
}
MONGO_CLIENT = MongoClient("mongodb://localhost:27017/")
mongo_db = MONGO_CLIENT["NominaColombia"]