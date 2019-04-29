#!/bin/bash
set -e

case "$1" in
    develop)
        echo "Running Development Server"
        echo -e "$EE_PRIVATE_KEY" | base64 -d > privatekey.pem
        exec python main.py
        ;;
    test)
        echo "Running tests"
        echo -e "$EE_PRIVATE_KEY" | base64 -d > privatekey.pem
        exec pytest --cov=gfwanalysis gfwanalysis/tests/
        ;;
    start)
        echo "Running Start"
        echo -e "$EE_PRIVATE_KEY" | base64 -d > privatekey.pem
        exec gunicorn -c gunicorn.py gfwanalysis:app
        ;;
    *)
        exec "$@"
esac
