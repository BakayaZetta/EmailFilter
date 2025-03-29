FROM python:3.11-slim
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN pip install --no-cache-dir -r /app/requirements.txt
RUN curl -fsSL https://ollama.com/install.sh |sh

WORKDIR /app

CMD ollama serve & sleep 5 &&  ollama pull deepseek-r1:1.5b &&  python3 deeptest.py
