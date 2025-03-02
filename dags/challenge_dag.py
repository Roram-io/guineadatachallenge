from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType
from pyspark.sql.functions import col, concat, lit, to_timestamp, from_utc_timestamp
from airflow import DAG
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.operators.python import PythonOperator
from google.cloud import storage
from sqlalchemy import create_engine
import pandas as pd
import io
import os
import tempfile
import papermill as pm

# La siguiente función descarga los datos sísmicos de bucket GCP a un DataFrame de PySpark.
def download_file(spark, **kwargs):
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
    except Exception as e:
        print("Error al descargar el archivo de GCP: ", e)
        return None
    return df

# Esta función sube el dataframe ya procesado a una base de datos Postgres.
def upload_to_postgres(spark, df): #Dataframe de spark. Se cambia a un Dataframe de Pandas para subirlo.
    postgres_url = "jdbc:postgresql://34.176.248.26:5432/guinea-challenge" #CREDENCIALES GCP
    postgres_properties = {
        "user": "postgres",
        "password": os.getenv("password"),
        "driver": "org.postgresql.Driver"
    }
    print("Intentando conectar a postgresql")
    df.write.jdbc(url=postgres_url, table="TBL_SEISMIC_DATA", mode="overwrite", properties=postgres_properties)

    return

# Se descarga los datos de sismos de GCP, se procesan (con Spark) y se guardan en una base de datos Postgres.
def process_file(**kwargs):
    spark = SparkSession.builder.appName("CSV to DataFrame").getOrCreate()
    df = download_file(spark, **kwargs)
    if (df==None):
        print("Error al descargar el archivo.")
        return
    print("DataFrame con datos descargados:")
    df.show() # Mostramos los datos descargados.
    df = df.dropna() # Eliminamos datos null, simplificado para efectos del challenge.
    df = df.filter((df.magnitud >= 4.0) & (df.magnitud <= 9.0)) #Filtramos sismos pequeños e irreales.
    # Transformación (para ejemplos del challenge). Cambiar UTC a Perú (Hora y Fecha).
    df = df.withColumn("fecha_peru",
        from_utc_timestamp(
            to_timestamp(concat(col("fecha_utc"), lit(" "), col("hora_utc")), "yyyy-MM-dd HH:mm:ss[.SSS]"),
            "America/Lima"
            )
    ).drop("fecha_utc", "hora_utc")
    print("DataFrame con datetime_peru:")
    df.show(truncate=False)
    print("Iniciando subida a PostgreSQL")
    upload_to_postgres(spark, df) # Guardamos en Postgres.
    spark.stop()
    return

#Subimos el ipynb ya ejecutado con papermill.
def upload_to_gcs(bucket_name, source_file, destination_blob):
    
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    
    # Subir archivo
    blob.upload_from_filename(source_file)
    print(f"✅ Archivo {source_file} subido a gs://{bucket_name}/{destination_blob}")

def execute_notebook(**kwargs):
    db_config = {
    "host": "34.176.248.26",         # Dirección del servidor PostgreSQL
    "port": 5432,                # Puerto de PostgreSQL
    "database": "guinea-challenge",  # Nombre de la base de datos
    "user": "postgres",        # Usuario de PostgreSQL
    "password": os.getenv("password")  # Contraseña de PostgreSQL
    }
    connection_string = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    engine = create_engine(connection_string)
    sql = "SELECT * FROM TBL_SEISMIC_DATA"
    try:
        df = pd.read_sql(sql, engine)
    except Exception as e:
        print("Error al leer datos de Postgres: ", e)
        return
    print("Dataframe con datos de sismos:")
    print(df)
    #Convertimos a parquet para ahorrar espacio.
    df.to_csv("processed_data.csv")
    pm.execute_notebook(
        "resources/template.ipynb",
        "procesed_data_report.ipynb",
        parameters=dict(data_path="data.csv")
    )
    upload_to_gcs(kwargs["bucket_name"], "procesed_data_report.ipynb", "procesed_data_report.ipynb")

    return

with DAG(
    dag_id="guinea_challenge",
    start_date=datetime(2024, 1, 1),
    schedule="0 9 * * *",
    catchup=False,
    default_args={"owner": "Astro", "retries": 1},
    tags=["Guinea_mobile"]
) as dag:
    
    kwargs = {
        "file_name": "datos.csv",
        "bucket_name": "bucket-guinea",
        "database": "guinea-challenge",
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
        op_kwargs=kwargs
    )

    run_ipynb_template = PythonOperator(
        task_id="run_ipynb_template",
        python_callable=execute_notebook,
        op_kwargs=kwargs
    )


    sensor_gcp >> process_and_save >> run_ipynb_template