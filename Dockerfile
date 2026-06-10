FROM python:3.11-slim
WORKDIR /app/todo_project
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY . /app
EXPOSE 5000
CMD ["python", "run.py"]