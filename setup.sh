#!/bin/bash

# This script automates the setup process for the Daydream web application.

# --- Step 1: Install Python dependencies ---
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

# --- Step 2: Create .env file ---
if [ -f ".env" ]; then
    echo ".env file already exists. Skipping creation."
else
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo ".env file created successfully."
fi

echo "Setup complete. Please configure your .env file with the necessary credentials."
