# Guinea Mobile - Data Challenge
Reto de flujo ETL para Guinea Mobile.

## Tabla de Contenidos

- [Instalación](#instalación)
- [Uso](#uso)
- [Descripción del Problema](#Descripción-del-Problema)
- [Tecnologías Escogidas](#Tecnologías-Escogidas)
- [Explicación de la Solución](#Explicación-De-La-Solución)

## Instalación
- IMPORTANTE
> Es necesario tener el archivo clave_super_secreta.json enviada al correo y copiarla al directorio raíz.

Para construir la imagen correr el siguiente comando

# AIRFLOW_PIP_ADDITIONAL_REQUIREMENTS=requirements.txt
` docker build -t guinea-challenge . ` 

Para ejecutar el contenedor correr el siguiente comando cambiando "Contraseña_provista" por la contraseña enviada por correo.

` docker run -d -p 8080:8080 -e PASSWORD="Contraseña_provista" --name airflow guinea-challenge `


Una vez esté ejecutado. Se puede acceder mediante 

[Localhost](http://localhost:8080) (Abrir en nueva pestaña)

## Descripción del Problema

El siguiente ETL se encarga de revisar la base de datos del Instituto Geofísico del Perú.
Se recibe un archivo .csv 

[Origen de Datos (Página del IGP)](https://ultimosismo.igp.gob.pe/descargar-datos-sismicos)

Este archivo está subido a un Bucket de GCP (Explicado más adelante) con el objetivo de simular que un tercero ha subido los archivos (como sucedería con la ingesta de datos en un caso real).
Los datos son ingeridos, limpiados, procesados y guardados en una base de datos para poder ser posteriormente procesados en un notebook para efectos de análisis de datos.

## Tecnologías Escogidas

Para resolver este problema se utilizan las siguientes tecnologías:

- Apache Airflow
> La herramienta de orquestación de mi preferencia, en este caso gestionado a través de Docker.

- Apache Spark
> Corrido de manera local, en un solo nodo, para efectos de prueba de datos.

- Docker 
> Para la creación de contenedores. Se elige la Imagen apache/airflow:2.7.1-python3.11.
> NOTA: Normalmente Spark necesitaría JDK y la instalación de Spark, pero al correr de forma
> local, no es necesario realizar pasos adicionales a la librería PySpark.

Las siguientes librerías son utilizadas (Presentes en requirements.txt)

- pyspark
> Interfaz de Spark utilizando python.

- google.cloud
> Con finalidad de conectarse a los servicios de GCP (Bucket)

- sqlalchemy
> Para conectarse a la base de datos y obtener el dataframe luego de ser procesado.

- pandas & pyplot
> Para los análisis de datos 

- io
> Para manejar los archivos como arreglos de Bytes en memoria.

## Explicación de la Solución

Pendiente...
