# Usar una imagen base con Java (requerido para Spark) y Python
FROM bitnami/spark:3.4.1

USER root
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    python3 \
    python3-pip \
    libpq-dev

# Instalar Astro CLI
RUN pip3 install astro-cli

# Copiar el archivo requirements.txt e instalar las dependencias de Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar todo el contenido del directorio actual al contenedor
COPY . .

EXPOSE 8080

# Comando por defecto para iniciar el servidor de desarrollo de Astro
CMD ["astro", "dev", "start"]