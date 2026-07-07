FROM python:3.12-slim
RUN pip install fastapi uvicorn pydantic
COPY server.py /app/server.py
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
