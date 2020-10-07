# GFW GEE Analysis

[![Build Status](https://travis-ci.org/gfw-api/gfw-analysis-gee.svg?branch=dev)](https://travis-ci.org/gfw-api/gfw-analysis-gee)
[![Test Coverage](https://api.codeclimate.com/v1/badges/2d03ef51b43e72eae7e1/test_coverage)](https://codeclimate.com/github/gfw-api/gfw-analysis-gee/test_coverage)

## Dependencies

Dependencies on other Microservices:

- [Geostore](https://github.com/gfw-api/gfw-geostore-api)

## Getting started

### Requirements

You need to install Docker in your machine if you haven't already [Docker](https://www.docker.com/)

### Development

Follow the next steps to set up the development environment in your machine.

1. Clone the repo and go to the folder

```ssh
git clone https://github.com/gfw-api/gfw-analysis-gee
cd gfw-analysis-gee
```

2. Run the gfwanalysis.sh shell script in development mode.

```ssh
./gfwanalysis.sh develop
```

If this is the first time you run it, it may take a few minutes.

### Tests

Run the tests via docker with:
```ssh
./gfwanalysis.sh test
```

Or natively via:
```ssh
pip install -r requirements.txt  --use-feature=2020-resolver
pip install -r requirements_dev.txt  --use-feature=2020-resolver
pytest --cov=gfwanalysis gfwanalysis/tests/
```

Testing requires a local Redis instance running with a `REDIS_URL` environment variable.

### Code structure

The API has been packed in a Python module (gfwanalysis). It creates and exposes a WSGI application. The core functionality
has been divided in three different layers or submodules (Routes, Services and Models).

There are also some generic submodules that manage the request validations, HTTP errors and the background tasks manager.
