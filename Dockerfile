FROM python:3.11
COPY ./src /app/src
ENV PYTHONPATH "${PYTHONPATH}:/app"
WORKDIR /app/src
RUN pip install -r requirements.txt
WORKDIR /app
ENTRYPOINT ["python3", "-m", "src.cli"]
