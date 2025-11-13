#!/bin/bash

# Activate the virtual environment
source venv/bin/activate

# Set the PYTHONPATH
export PYTHONPATH=$(pwd)

# Run the seeding script
python seed_persona_quiz.py

# Deactivate the virtual environment
deactivate
