FROM python:2.7

MAINTAINER Sergio Gordillo sergio.gordillo@vizzuality.com

# Copy the application folder inside the container
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN mkdir /src
COPY /src /src
COPY privatekey.pem .

# Expose port
EXPOSE 8080

# Launch script
ENTRYPOINT ["python"]
CMD ["./src/main.py"]
