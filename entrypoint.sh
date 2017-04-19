#!/bin/bash
set -e

case "$1" in
    develop)
        echo "Running Development Server"
        echo -e "$EE_PRIVATE_KEY" | base64 -d > privatekey.pem
        exec python main.py
        ;;
    test)
        echo "Test (not yet)"
        ;;
    start)
        echo "Running Start"
        echo -e "$EE_PRIVATE_KEY" | base64 -d > privatekey.pem
        exec gunicorn -c gunicorn.py gfwumd:app
        ;;
    *)
        exec "$@"
esac
