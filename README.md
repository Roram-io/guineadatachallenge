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

` docker build -t guinea-challenge . ` 

Para ejecutar el contenedor correr el siguiente comando cambiando "Contraseña_provista" por la contraseña enviada por correo.

` docker run -d -p 8080:8080 -e password="Contraseña_provista" --name airflow guinea-challenge `


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

Construimos la imagen utilizando el .json y la contraseña explicados en la primera sección.

![Comando de Build](https://imgur.com/tIUepdi.png)
![Comando de Run](https://imgur.com/PHdhttt.png)

Luego ingresamos a [Airflow](http://localhost:8080)
Con las credenciales 
> admin
> admin

![Inicio de Airflow](https://imgur.com/oYjspHO.png)

Podemos observar un único DAG, lo activamos. Los resultados son idempotentes, por lo que debería mostrarse el siguiente gráfico.

![DAG del Challenge](https://imgur.com/h3JgIgd.png)
![Resultado](https://imgur.com/ir1240g.png)

El dag ejecutará un sensor para detectar la subida de los datos en crudo (subidos previamente para efectos del challenge).
Procederá al procesamiento de los datos.

- Datos crudos (Horario UTC, valores menores a 4 y mayores a 9)
![Datos Crudos](https://imgur.com/COgGvsN.png)

- Datos procesados utilizando pySpark (Datetime de Peru, valores significantes)
![Datos Procesados](https://imgur.com/UKmdbdL.png)

- Se suben los datos ya procesados a postgreSQL.

![Subida PostgreSQL](https://imgur.com/Lza0DfX.png)

- Posteriormente, se ejecutará la siguiente task que procesa un notebook ipynb con un análisis estadístico.
- Se tiene una plantilla 'template.ipynb'.
![Plantilla Notebook](https://imgur.com/UUd8TXM.png)

- El task descarga desde la base de datos PostgreSQL (Podría ser en un contexto de que estos datos volvieron a ser 'procesados' por un tercero)
- Vuelve el dataframe un archivo .csv para que pueda ser enviado como parámetro al notebook.
- Se ejecuta el notebook.
- Finalmente, el resultado del notebook procesado es subido al mismo bucket GCP.
![Notebook Ejecutado](https://imgur.com/g3Batvb.png)

Mira la magia. [Click](https://storage.googleapis.com/bucket-guinea/procesed_data_report.ipynb)


