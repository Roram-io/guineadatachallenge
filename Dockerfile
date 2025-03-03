# Usar la imagen oficial de Apache Airflow
FROM apache/airflow:2.7.1-python3.11

USER root
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Instalar OpenJDK 11 y limpiar caché
RUN apt-get update && apt-get install -y openjdk-11-jdk procps && apt-get clean 

# Configurar JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-arm64
ENV PATH=$PATH:$JAVA_HOME/bin

# Copiar la carpeta "dags", "jar" y "resources" al directorio de Airflow
COPY dags /opt/airflow/dags
COPY requirements.txt /requirements.txt
COPY dags/resources/postgresql-42.7.5.jar /opt/airflow/jars/postgresql-42.7.5.jar
COPY clave_super_secreta.json /opt/airflow/clave_super_secreta.json

# Instalar dependencias adicionales (si es necesario)
USER airflow
RUN pip install notebook
RUN pip install -r /requirements.txt

# Esta variable se envía a la imagen de Airflow para que pueda acceder a la clave de Google Cloud, solo para efectos del challenge.
ENV GOOGLE_APPLICATION_CREDENTIALS="/opt/airflow/clave_super_secreta.json" 

#Ejecutamos Linter
RUN pylint /opt/airflow/dags

ENTRYPOINT ["/entrypoint.sh"]