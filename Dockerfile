FROM python:3.10-slim

# Evitar escritura de archivos .pyc y asegurar que los logs se emitan directamente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instalar dependencias del sistema (las originales + las requeridas por Playwright y msodbcsql)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgl1 \
    libglib2.0-0 \
    git \
    curl \
    wget \
    gnupg \
    libnss3 \
    libatk-bridge2.0-0 \
    libxkbcommon0 \
    libgtk-3-0 \
    libgbm1 \
    libasound2 \
    libxshmfence1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libdrm2 \
    libxfixes3 \
    libxext6 \
    libx11-6 \
    libxcb1 \
    unixodbc \
    unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar msodbcsql18 para SQL Server
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Instalar uv desde la imagen oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copiar requirements.txt e instalar dependencias usando uv a nivel de sistema
COPY requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

# Copiar el código del proyecto
COPY . .

# Exponer el puerto del servidor web
EXPOSE 8000

# Comando para iniciar la API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

