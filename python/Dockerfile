# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Verify installation of necessary packages
RUN pip list




# Copy the current directory contents into the container at /app
COPY . /app

# Expose ports for Streamlit and Uvicorn
EXPOSE 8000 8501