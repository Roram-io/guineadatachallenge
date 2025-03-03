#!/bin/bash

# Iniciar la base de datos de Airflow
airflow db init

# Crear el usuario de Airflow (si no existe)
airflow users create \
    --username admin \
    --firstname Guinea \
    --lastname Mobile \
    --role Admin \
    --email test@example.com \
    --password admin || true

# Iniciar los servicios de Airflow
airflow scheduler & airflow webserver --port 8080