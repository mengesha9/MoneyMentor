# Dockerfile for Python backend
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy the contents
COPY . .

# Add app directory to PYTHONPATH
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port for Cloud Run
EXPOSE 8080

# Start the FastAPI app with uvicorn using Python entrypoint
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8080"]
