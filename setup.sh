#!/bin/bash

# This script automates the setup process for the Daydream web application.

# Function to print colored output
print_message() {
    COLOR=$1
    MESSAGE=$2
    NC='\033[0m' # No Color
    case $COLOR in
        "green")
            echo -e "\033[0;32m${MESSAGE}${NC}"
            ;;
        "red")
            echo -e "\033[0;31m${MESSAGE}${NC}"
            ;;
        "blue")
            echo -e "\033[0;34m${MESSAGE}${NC}"
            ;;
        *)
            echo "${MESSAGE}"
            ;;
    esac
}

# --- Step 1: Check for Python and Pip ---
print_message "blue" "Step 1: Checking for Python and Pip..."
if ! command -v python3 &> /dev/null
then
    print_message "red" "Error: python3 is not installed. Please install Python 3 and try again."
    exit 1
fi

if ! command -v pip3 &> /dev/null
then
    print_message "red" "Error: pip3 is not installed. Please install pip3 and try again."
    exit 1
fi
print_message "green" "Python and Pip are installed."

# --- Step 2: Set up Virtual Environment ---
VENV_DIR="venv"
print_message "blue" "Step 2: Setting up virtual environment..."
if [ -d "$VENV_DIR" ]; then
    print_message "green" "Virtual environment '$VENV_DIR' already exists. Activating..."
else
    print_message "blue" "Creating virtual environment '$VENV_DIR'..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        print_message "red" "Error: Failed to create virtual environment."
        exit 1
    fi
    print_message "green" "Virtual environment created successfully."
fi

# Activate the virtual environment
source $VENV_DIR/bin/activate
print_message "green" "Virtual environment activated."

# --- Step 3: Install Python dependencies ---
print_message "blue" "Step 3: Installing Python dependencies from requirements.txt..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    print_message "red" "Error: Failed to install dependencies."
    exit 1
fi
print_message "green" "Dependencies installed successfully."

# --- Step 4: Create .env file ---
print_message "blue" "Step 4: Creating .env file..."
if [ -f ".env" ]; then
    print_message "green" ".env file already exists. Skipping creation."
else
    print_message "blue" "Creating .env file from .env.example..."
    cp .env.example .env
    print_message "green" ".env file created successfully."
fi

print_message "green" "\nSetup complete!"
print_message "blue" "To activate the virtual environment in your shell, run:"
print_message "blue" "source $VENV_DIR/bin/activate"
print_message "blue" "Please configure your .env file with the necessary credentials."
