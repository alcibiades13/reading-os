#!/usr/bin/env bash
# exit on error
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Collect static files (does not need database)
python manage.py collectstatic --no-input

# NOTE: migrations moved to preDeployCommand in render.yaml
# because the internal DB hostname is not available during build
