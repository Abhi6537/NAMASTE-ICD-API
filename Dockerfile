# Use an official Python runtime as a parent image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces the image size by not storing the pip cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable (optional, can be set in docker-compose or directly)
ENV PYTHONUNBUFFERED=1

# Run the application using uvicorn
# The command to run your application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]