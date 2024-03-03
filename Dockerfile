FROM python:3

RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN apt-get install libpq-dev
RUN pip install -r requirements.txt
COPY . /app