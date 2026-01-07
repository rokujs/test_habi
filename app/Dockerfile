FROM python:3.12.12-slim-bookworm

# Instalar dependencias del sistema necesarias para psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download the latest installer
ADD https://astral.sh/uv/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

COPY ./.bashrc /root/

WORKDIR /opt/project
COPY ./pyproject.toml ./uv.lock ./.python-version ./
RUN /root/.local/bin/uv sync

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod u+x /docker-entrypoint.sh

# Set the default command to run when the container starts
# ENTRYPOINT ["/docker-entrypoint.sh"]

# Set the default command to keep the container running
ENTRYPOINT [ "sleep", "infinity" ]