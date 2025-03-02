# Usar la imagen oficial de Apache Airflow
FROM apache/airflow:2.7.1-python3.11

USER root
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
# Copiar la carpeta "dags" y "resources" al directorio de Airflow
COPY dags /opt/airflow/dags
COPY requirements.txt /requirements.txt

# Instalar dependencias adicionales (si es necesario)
USER airflow
RUN pip install --no-cache-dir notebook  # Instalar Jupyter Notebook si necesitas usarlo

RUN pip install --no-cache-dir -r /requirements.txt

ENTRYPOINT ["/entrypoint.sh"]