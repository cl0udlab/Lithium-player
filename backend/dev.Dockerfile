FROM python:3.12-bookworm as build

RUN pip install poetry==2.5.1

COPY --from=denoland/deno:bin-2.5.6 /deno /usr/local/bin/deno


ENV PYTHONPATH=/app/src \
    WATCHFILES_FORCE_POLLING=true

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN poetry install


WORKDIR /app/src
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
