FROM python:3.9-slim

WORKDIR /app

COPY ./api/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./api /app/api
COPY ./gebaeude.din18599.schema.json /app/gebaeude.din18599.schema.json

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
