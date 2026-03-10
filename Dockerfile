FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
ENV PYTHONPATH=/app

COPY ./pyproject.toml ./uv.lock ./.python-version /app/
RUN uv sync


COPY mailsender/ /app/mailsender

CMD [ "uv", "run", "fastapi", "run", "mailsender/api/main.py" ]
