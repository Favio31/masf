# Imagen base: Python 3.12 (slim para menor tamaño)
FROM python:3.12-slim

# Directorio de trabajo en el contenedor
WORKDIR /app

# Instalar dependencias del sistema (si fueran necesarias)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero (mejor cache de Docker)
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY core/ ./core/
COPY profiles/ ./profiles/
COPY clients/ ./clients/
COPY drafts/ ./drafts/
COPY published/ ./published/

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Comando por defecto (puede sobrescribirse)
CMD ["python", "-m", "core.main", "--help"]
