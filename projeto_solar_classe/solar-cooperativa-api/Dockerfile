FROM python:3.12-slim

# Instala o uv diretamente da imagem oficial
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Variáveis para otimizar o uv no container
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Copia primeiro os arquivos de dependência para aproveitar cache de layers
COPY pyproject.toml ./

# Cria o ambiente virtual e instala as dependências
RUN uv sync --no-install-project

# Copia o restante do código
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY entrypoint.sh ./

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]