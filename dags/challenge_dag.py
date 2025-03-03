""" Este script contiene el DAG que ejecuta el flujo de trabajo del challenge de Guinea Mobile. """
import io
import os
import tempfile
from datetime import datetime
import papermill as pm
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType
from pyspark.sql.functions import col, concat, lit, to_timestamp, from_utc_timestamp
from google.cloud import storage
from google.api_core.exceptions import GoogleAPICallError
from sqlalchemy import create_engine
import resources.settings as SETTINGS
from airflow import DAG
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.operators.python import PythonOperator

os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-11-openjdk-arm64"

def download_file(spark, **kwargs):
    """La siguiente función descarga los datos sísmicos de bucket GCP a un DataFrame de PySpark."""
    schema = StructType([ #Definimos un esquema para asegurar la integridad de los datos.
    StructField("fecha_utc", StringType(), True),
    StructField("hora_utc", StringType(), True),
    StructField("latitud", FloatType(), True),
    StructField("longitud", FloatType(), True),
    StructField("profundidad", IntegerType(), True),
    StructField("magnitud", FloatType(), True)
    ])
    try:
        client = storage.Client()
        bucket = client.bucket(kwargs["bucket_name"])
        blob = bucket.blob(kwargs["file_name"])
        buffer = io.BytesIO()
        blob.download_to_file(buffer)
        buffer.seek(0)
        print("Descarga de GCP realizada")

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp.write(buffer.getvalue())
            tmp.flush()
            tmp_path = tmp.name
        # Leer el archivo CSV con Spark (asumiendo que tiene header)
        df = spark.read.schema(schema).option("header", "true").csv(tmp_path)
    except FileNotFoundError as e:
        print("Error al descargar el archivo de GCP: ", e)
    except GoogleAPICallError as e:
        print("Error al descargar el archivo de GCP: ", e)
    return df


def upload_to_postgres(df):
    """ Esta función sube el dataframe ya procesado a una base de datos Postgres.
    Dataframe de spark. Se cambia a un Dataframe de Pandas para subirlo. """
    postgres_url = SETTINGS.POSTGRES_URL #CREDENCIALES Postgres
    postgres_properties = {
        "user": SETTINGS.POSTGRES_USER,
        "password": os.getenv("password"),
        "driver": SETTINGS.POSTGRES_DRIVER
    }
    print("Intentando conectar a postgresql")
    df.write.jdbc(url=postgres_url,
                  table=SETTINGS.TABLE_NAME,
                  mode="overwrite",
                  properties=postgres_properties)


def process_file(**kwargs):
    """ Se descarga los datos de sismos de GCP, se procesan (con Spark)
    y se guardan en una base de datos Postgres. """
    spark = SparkSession.builder \
    .master("local[*]") \
    .appName("CSV-to-DataFrame") \
    .config("spark.jars", "/opt/airflow/jars/postgresql-42.7.5.jar") \
    .config("spark.driver.extraClassPath", "/opt/airflow/jars/postgresql-42.7.5.jar") \
    .config("spark.executor.extraClassPath", "/opt/airflow/jars/postgresql-42.7.5.jar") \
    .config("spark.driver.memory", "1g") \
    .getOrCreate()
    df = download_file(spark, **kwargs)
    if df is None:
        print("Error al descargar el archivo.")
        return
    print("DataFrame con datos descargados:")

    df.show() # Mostramos los datos descargados.
    # Eliminamos datos null, simplificado para efectos del challenge.
    df = df.dropna()
    # Filtramos sismos pequeños e irreales.
    df = df.filter((df.magnitud >= 4.0) & (df.magnitud <= 9.0))
    # Transformación (para ejemplos del challenge). Cambiar UTC a Perú (Hora y Fecha).
    df = df.withColumn("fecha_peru",
        from_utc_timestamp(
            to_timestamp(concat(col("fecha_utc"),
                                lit(" "),
                                col("hora_utc")),
                                "yyyy-MM-dd HH:mm:ss[.SSS]"),
            "America/Lima"
            )
    ).drop("fecha_utc", "hora_utc")
    print("DataFrame con datetime_peru:")
    df.show(truncate=False)
    print("Iniciando subida a PostgreSQL")
    upload_to_postgres(df) # Guardamos en Postgres.
    spark.stop()


def upload_to_gcs(bucket_name, source_file, destination_blob):
    """ Sube el archivo a un bucket de Google Cloud Storage. """

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    # Subir archivo
    blob.upload_from_filename(source_file)
    print(f"✅ Archivo {source_file} subido a gs://{bucket_name}/{destination_blob}")


def execute_notebook(**kwargs):
    """ Ejecuta un notebook de Jupyter con Papermill y sube el resultado a GCS. """
    db_config = {
    "host": SETTINGS.DB_HOST,         # Dirección del servidor PostgreSQL
    "port": SETTINGS.DB_PORT,                # Puerto de PostgreSQL
    "database": SETTINGS.DB_DATABASE,  # Nombre de la base de datos
    "user": SETTINGS.DB_USER,        # Usuario de PostgreSQL
    "password": os.getenv("password")  # Contraseña de PostgreSQL
    }
    connection_string = (f"postgresql+psycopg2://{db_config['user']}:"
                         f"{db_config['password']}@{db_config['host']}:"
                         f"{db_config['port']}/{db_config['database']}")
    engine = create_engine(connection_string)

    #Puede venir de una variable, para efectos del challenge se deja aquí.
    sql = "SELECT * FROM TBL_SEISMIC_DATA"
    conn = engine.raw_connection()
    df = pd.read_sql(sql, conn)
    print("Dataframe con datos de sismos:")
    print(df)
    conn.close()
    #Convertimos a .csv para subirlo a s3
    df.to_csv(SETTINGS.CSV_FILE_NAME, index=False)
    print("Ejecutando Notebook")
    # Directorio absoluto para evitar problemas con direcciones relativas.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(base_dir, "resources", SETTINGS.NOTEBOOK_TEMPLATE)
    pm.execute_notebook(
        template_path,
        SETTINGS.NOTEBOOK_OUTPUT,
        parameters={"data_path" : SETTINGS.CSV_FILE_NAME}
    )
    print("Subiendo notebook resultante a GCS")
    upload_to_gcs(kwargs["bucket_name"], SETTINGS.NOTEBOOK_OUTPUT, SETTINGS.NOTEBOOK_OUTPUT)
    print("¡Terminado! :)")

with DAG(
    dag_id=SETTINGS.DAG_ID,
    start_date=datetime(2024, 1, 1),
    schedule="0 9 * * *",
    catchup=False,
    default_args={"owner": "Guinea", "retries": 1},
    tags=["Guinea_mobile"]
) as dag:

    args = {
        "file_name": SETTINGS.FILE_NAME,
        "bucket_name": SETTINGS.BUCKET_NAME,
        "database": SETTINGS.DATABASE,
    }

    sensor_gcp = GCSObjectExistenceSensor(
        task_id="sensor_gcp",
        bucket="bucket-guinea",
        object="datos.csv",
        timeout=600,
        poke_interval=60
    )

    process_and_save = PythonOperator(
        task_id="limpieza_de_datos",
        python_callable=process_file,
        op_kwargs=args
    )

    run_ipynb_template = PythonOperator(
        task_id="run_ipynb_template",
        python_callable=execute_notebook,
        op_kwargs=args
    )

    sensor_gcp >> process_and_save >> run_ipynb_template # pylint: disable=pointless-statement
