FROM python:3.11-slim
WORKDIR /app/todo_project
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
RUN mkdir -p /app/todo_project/instance && \
    chown -R nobody:nogroup /app

# Variáveis de ambiente para o Flask mapear o caminho correto
ENV FLASK_APP=run.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# REQUISITO DE SEGURANÇA: Altera o utilizador para não-root (nobody)
USER nobody

EXPOSE 5000
CMD ["python", "run.py"]