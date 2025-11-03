# Gunakan base image Python
FROM python:3.9-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install dependensi sistem
RUN apt-get update \
    && apt-get -y install netcat-traditional \
    && apt-get clean

# Install dependensi Python
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

# Berikan izin eksekusi untuk entrypoint script
RUN chmod +x /app/entrypoint.sh

# Jalankan entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]