FROM python:3.12-slim

WORKDIR /app

RUN apt update && apt install -y --no-install-recommends ca-certificates git && update-ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN apt purge git -y  && apt autoremove -y

COPY captcha-solver.py .

EXPOSE 8080

CMD ["python", "captcha-solver.py"]
