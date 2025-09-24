# Stage 1: Build the application
FROM python:3.9-slim as builder

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy only pyproject.toml and poetry.lock to leverage Docker cache
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi

# Copy the rest of the application
COPY . .

# Stage 2: Create the final image
FROM python:3.9-slim

WORKDIR /app

# Copy the installed dependencies from the builder stage
COPY --from=builder /app /app

# Expose the port the app runs on
EXPOSE 80

# Command to run the application
CMD ["uvicorn", "opengovfood.main:app", "--host", "0.0.0.0", "--port", "80"]
