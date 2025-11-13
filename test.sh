#!/bin/bash

# This script automates the testing process for the Daydream web application.

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

VENV_DIR="venv"

# --- Step 1: Activate Virtual Environment ---
print_message "blue" "Step 1: Activating virtual environment..."
if [ -d "$VENV_DIR" ]; then
    source $VENV_DIR/bin/activate
    print_message "green" "Virtual environment activated."
else
    print_message "red" "Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# --- Step 2: Set PYTHONPATH ---
print_message "blue" "Step 2: Setting PYTHONPATH..."
export PYTHONPATH=$PYTHONPATH:.
print_message "green" "PYTHONPATH set."

# --- Step 3: Run tests ---
print_message "blue" "Step 3: Running tests..."
pytest tests/
if [ $? -ne 0 ]; then
    print_message "red" "Error: Tests failed."
    deactivate
    exit 1
fi
print_message "green" "Tests passed successfully."

# --- Step 4: Deactivate Virtual Environment ---
print_message "blue" "Step 4: Deactivating virtual environment..."
deactivate
print_message "green" "Virtual environment deactivated."

print_message "green" "\nTesting complete!"
