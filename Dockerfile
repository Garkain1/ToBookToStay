FROM python:3.11
RUN apt-get update && apt-get install -y netcat-openbsd
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . /app/
RUN chmod +x /app/wait_for_db.sh
CMD ["sh", "/app/wait_for_db.sh", "python", "manage.py", "runserver", "0.0.0.0:8000"]