FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y --fix-missing default-jre-headless && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ВАЖНО: Файл antlr-4.13.2-complete.jar должен лежать рядом с Dockerfile
COPY Transliatory.g4 .
COPY antlr-4.13.2-complete.jar .

RUN java -jar antlr-4.13.2-complete.jar -Dlanguage=Python3 -visitor Transliatory.g4

COPY analyzer.py .
COPY run_all_tests.py .
COPY examples/ ./examples/

CMD ["python", "run_all_tests.py"]