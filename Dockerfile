# syntax=docker/dockerfile:1

FROM python:3.12.4


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /home/app/webapp

# Install dependencies first (cacheable)
COPY requirements.txt ./
# RUN pip install --upgrade pip \
#  && pip install --no-cache-dir -r requirements.txt
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .


# Expose port and define default command
EXPOSE 80
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:80 --timeout 120"]
