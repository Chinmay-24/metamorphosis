FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt setup.py ./
RUN pip install -e .

COPY . .

EXPOSE 7860

CMD ["uvicorn", "spaces_app:app", "--host", "0.0.0.0", "--port", "7860"]
