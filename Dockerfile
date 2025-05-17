FROM python:3.12-slim

WORKDIR /app

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git && update-ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt purge git && apt autoremove

COPY captcha-solver.py .

EXPOSE 8080

CMD ["python", "captcha-solver.py"]
