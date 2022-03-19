FROM python:3.10

WORKDIR /app

# Install poetry
RUN pip3 install poetry

# Install deps
COPY pyproject.toml poetry.lock .
RUN poetry install --no-dev

# Set timezone to BST
ENV TZ Europe/London

# Add source
COPY . .

CMD poetry run python main.py
