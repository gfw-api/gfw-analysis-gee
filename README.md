# GFW GEE Analysis

In progress..

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

Or nativley via:
```ssh
pip install -r requirements.txt
pytest --cov=gfwanalysis gfwanalysis/tests/
```

### Code structure

The API has been packed in a Python module (gfwanalysis). It creates and exposes a WSGI application. The core functionality
has been divided in three different layers or submodules (Routes, Services and Models).

There are also some generic submodules that manage the request validations, HTTP errors and the background tasks manager.
