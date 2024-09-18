# Use the official Python image as a base image
FROM python:3.11-slim

# Install Rust, Maturin, and other necessary tools
# Install dependencies for building Rust packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libssl-dev \
    python3-dev \
    && curl https://sh.rustup.rs -sSf | sh -s -- -y \
    && source $HOME/.cargo/env \
    && rustup default stable \
    && rustup update stable \
    && pip install maturin

WORKDIR /app
COPY . .

WORKDIR /app/geoprop-py
RUN maturin build
RUN pip install target/wheels/geoprop_py-*.whl

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Expose the FastAPI port
EXPOSE 8080

# Command to run FastAPI using uvicorn on port 8080
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
