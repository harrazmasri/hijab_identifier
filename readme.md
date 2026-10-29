create dockerfile

# Use the official Python slim image as the base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (needed for build tools, database drivers, or image processing libraries like OpenCV)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the Django project code into the container
COPY . /app/

# Expose the port Django runs on
EXPOSE 8000

# Run migrations and start the development server (or use Gunicorn for production)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

create .dockerignore

venv/
env/
__pycache__/
*.pyc
*.sqlite3
.git
.gitignore
media/

create requirements.txt

Django>=4.2
gunicorn
psycopg2-binary

docker build -t hijab-identifier .

docker run -d -p 8000:8000 --name hijab-app hijab-identifier

# Stop/remove any existing container first
docker stop hijab-app && docker rm hijab-app

# Run with a volume mount for live reloading
docker run -d -p 8000:8000 -v $(pwd):/app --name hijab-app hijab-identifier

docker exec -it hijab-app python manage.py makemigrations

docker exec -it hijab-app python manage.py showmigrations

docker exec -it hijab-app python manage.py migrate

docker exec -it hijab-app python manage.py createsuperuser

docker logs hijab-app

docker stop hijab-app

docker rm hijab-app