# Minimal API-Image: installiert nur die Python-Abhaengigkeiten.
# Der Anwendungscode wird via docker-compose als Volume (./api -> /app)
# gemountet, das Start-Command (uvicorn main:app --reload) kommt aus der
# docker-compose.yml. Deshalb genuegt hier das Dependency-Layer.
FROM python:3.11-slim

WORKDIR /app

# Build-Tools fuer psycopg2/ifcopenshell-Abhaengigkeiten
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
