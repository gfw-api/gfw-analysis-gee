FROM python:2.7-alpine

MAINTAINER Sergio Gordillo sergio.gordillo@vizzuality.com

RUN apk update && apk upgrade && \
   apk add --no-cache --update bash git openssl-dev build-base alpine-sdk libffi-dev

# Copy the application folder inside the container
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY /src /src
COPY /microservice /microservice
COPY entrypoint.sh .

# Expose port
EXPOSE 8080

VOLUME /src
VOLUME /microservice

# Launch script
ENTRYPOINT ["./entrypoint.sh"]
