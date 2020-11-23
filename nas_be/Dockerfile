# pull official base image
FROM python:3.6

WORKDIR /usr/src/app

#ENV PYTHONDONTWRITEBYTECODE
#ENV PYTHONUNBUFFERED 1
#RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

RUN pip install --upgrade pip

COPY ./app/ /usr/src/app/

#RUN export LDFLAGS="-L/usr/local/opt/openssl/lib"

RUN pip install -r requirements.txt

EXPOSE 5000

CMD python app_test.py
