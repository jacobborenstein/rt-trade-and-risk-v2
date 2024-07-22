# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

COPY /tickers.txt /app/python/tickers.txt

# Install any needed packages specified in requirements.txt
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt    3

# Expose ports for Streamlit and Uvicorn
EXPOSE 8000 8501
