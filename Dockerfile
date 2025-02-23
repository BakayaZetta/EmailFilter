FROM python:3.11-slim

WORKDIR /detectish

RUN apt-get update && apt-get install -y make build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements-huggingface.txt requirements-base.txt ./
RUN pip install --no-cache-dir -r requirements-huggingface.txt && \
    pip install --no-cache-dir -r requirements-base.txt

COPY ./src ./src
COPY ./phishing_email_example ./phishing_email_example

CMD ["python", "analysis/ai_analysis/ai_analysis.py"]
