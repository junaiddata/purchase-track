#!/bin/bash

# Stock Update Script for Linux VPS
# This script runs the Django management command to update stock data

# Set the project directory (CHANGE THIS TO YOUR ACTUAL PATH)
PROJECT_DIR="/var/www/purchase-track"

# Set the virtual environment path (CHANGE THIS TO YOUR ACTUAL PATH)
VENV_PATH="/var/www/purchase-track/venv"

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment
source "$VENV_PATH/bin/activate" || exit 1

# Run the management command
python manage.py import_stock_api

# Deactivate virtual environment
deactivate

# Exit with success
exit 0
