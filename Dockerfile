FROM python:3.11
COPY ./src /app
ENV PYTHONPATH "${PYTHONPATH}:/app"
WORKDIR /app
RUN pip install -r requirements.txt