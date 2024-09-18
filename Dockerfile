FROM python:3.11-slim

ENV HOME="/root"

# rust and cargo
RUN apt-get update && \
    apt-get install -y curl build-essential && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y && \
    echo '. "$HOME/.cargo/env"' >> ~/.bashrc && \
    . "$HOME/.cargo/env" && \
    apt-get clean

ENV PATH="$HOME/.cargo/bin:$PATH"

RUN pip install --upgrade pip
RUN pip install maturin

WORKDIR /app
COPY . .

# build geoprop-py using maturin
WORKDIR /app/geoprop-py
RUN maturin build
RUN pip install target/wheels/geoprop-*-manylinux*.whl

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
