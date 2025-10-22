FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV PYTHONPATH=/app

COPY ./pyproject.toml ./uv.lock ./.python-version /app/
RUN uv sync


COPY . /app

CMD [ "uv", "run", "fastapi", "run", "main.py" ]
