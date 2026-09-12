# Stage 1: builder
FROM python:3.14-slim AS builder

# Set the working directory
WORKDIR /app

# Install uv for dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Create a virtual environment and install dependencies
# using uv. By default uv creates .venv if VIRTUAL_ENV is not set, but we can be explicit
ENV VIRTUAL_ENV=/app/.venv
RUN uv venv $VIRTUAL_ENV && \
    uv pip install -r pyproject.toml

# Stage 2: runtime
FROM python:3.14-slim AS runtime

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Update PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application source code
COPY . .

# Expose the application port
EXPOSE 8000

# Start the FastAPI application
CMD ["uvicorn", "smartrouter.main:app", "--host", "0.0.0.0", "--port", "8000"]
