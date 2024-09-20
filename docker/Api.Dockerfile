# First stage: Build stage
FROM python:3.12.6-slim AS build-stage

RUN useradd -m fastapi

WORKDIR /home/fastapi/app

# Copy the application code and install dependencies in the build stage
COPY ./api /home/fastapi/app
RUN pip install --no-cache-dir -r requirements.txt

# Set proper file permissions (read and execute only by the fastapi user)
RUN chmod -R 550 /home/fastapi/app

# Second stage: Runtime stage
FROM python:3.12.6-slim

# Recreate the fastapi user in the second stage
RUN useradd -m fastapi

# Copy the Python environment (dependencies) from the build stage
COPY --from=build-stage /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build-stage /usr/local/bin /usr/local/bin

# Copy the application code and dependencies from the build stage
COPY --from=build-stage /home/fastapi/app /home/fastapi/app

# Ensure permissions are preserved
RUN chown -R fastapi:fastapi /home/fastapi/app
RUN chmod -R 550 /home/fastapi/app

# Switch to non-root user
USER fastapi
WORKDIR /home/fastapi/app

# Expose port 80 for the API
EXPOSE 80

# Run the API
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
