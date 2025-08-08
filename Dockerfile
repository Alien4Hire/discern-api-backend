FROM python:3.11-bullseye

WORKDIR /app

# System deps
RUN apt-get update && apt-get upgrade -y && apt-get install -y \
    wget make gcc libreadline-dev libsqlite3-dev curl \
    && apt-get clean

# Build SQLite >= 3.35.0 (Chroma requires)
# (Keep this pinned; if SQLite URL breaks again, bump the version)
RUN wget https://www.sqlite.org/2024/sqlite-autoconf-3450300.tar.gz \
    && tar xzf sqlite-autoconf-3450300.tar.gz \
    && cd sqlite-autoconf-3450300 \
    && ./configure --prefix=/usr/local \
    && make -j"$(nproc)" \
    && make install \
    && cd .. \
    && rm -rf sqlite-autoconf-3450300 sqlite-autoconf-3450300.tar.gz

ENV LD_LIBRARY_PATH="/usr/local/lib"

# Python deps
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY ./api /app/api
COPY ./crew /app/crew
COPY ./elastic /app/elastic
# DO NOT bake secrets into the image.
# Use env vars / env_file in compose instead.

EXPOSE 8000
# Command overridden by docker-compose for loader; API uses uvicorn command in compose.
CMD ["python", "-c", "print('Image built. Use docker-compose services to run API or loader.')"]
