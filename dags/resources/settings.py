""" Configuración de parámetros de conexión para proceso ETL. """

DAG_ID = "guinea_challenge"

FILE_NAME = "datos.csv"

BUCKET_NAME = "bucket-guinea"
DATABASE = "guinea-challenge"

#Datos de la base de datos para JDBC.
POSTGRES_URL = "jdbc:postgresql://34.176.248.26:5432/postgres"
POSTGRES_USER = "postgres"
POSTGRES_DRIVER = "org.postgresql.Driver"

#Datos de la base de datos para SQLAlchemy.
DB_HOST = "34.176.248.26"
DB_PORT = 5432
DB_DATABASE = "postgres"
DB_USER = "postgres"

TABLE_NAME = "TBL_SEISMIC_DATA"

#Datos del notebook

CSV_FILE_NAME = "processed_data.csv"
NOTEBOOK_TEMPLATE = "template.ipynb"
NOTEBOOK_OUTPUT = "procesed_data_report.ipynb"
