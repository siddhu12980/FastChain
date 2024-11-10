FROM python:3.12.7-bookworm

WORKDIR /app

COPY ./app/requirements.txt .

RUN pip install --upgrade pip

RUN pip install -r requirements.txt


COPY . .

EXPOSE 3005

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3005"]