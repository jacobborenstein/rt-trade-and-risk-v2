# Use an official Python runtime as a parent image
FROM python:3-slim

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY ./code/requirements.txt /project/requirements.txt
RUN python -m pip install -r /project/requirements.txt

# Set the working directory in the container
WORKDIR /project

# Copy the code directory contents into the container at /project
COPY ./code /project

# Creates a non-root user with an explicit UID and adds permission to access the /project folder
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /project
USER appuser

# Default command (can be overridden by docker-compose)
CMD ["python", "/project/price_publisher.py"]