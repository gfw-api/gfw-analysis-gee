FROM python:2.7

MAINTAINER Sergio Gordillo sergio.gordillo@vizzuality.com

# Copy the application folder inside the container
RUN mkdir /src
COPY /src /src
COPY requirements.txt .
COPY privatekey.pem .

# Get pip to download and install requirements:
RUN pip install -r requirements.txt

# Expose ports
EXPOSE 8080

# Launch script
ENTRYPOINT ["python"]
CMD ["./src/main.py"]
