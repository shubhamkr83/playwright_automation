FROM python:3.10.15-slim-bullseye
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update 
COPY . .
RUN pip install -r requirements.txt
RUN  playwright install-deps && playwright install
CMD [ "python", "-u", "main.py" ]
