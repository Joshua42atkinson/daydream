# Contributing to Daydream

We welcome contributions from the community! Whether you're fixing a bug, adding a new feature, or improving the documentation, your help is appreciated.

## Getting Started

### 1. Fork and Clone the Repository

First, fork the repository to your own GitHub account. Then, clone your fork to your local machine:

```bash
git clone https://github.com/YOUR_USERNAME/daydream.git
cd daydream
```

### 2. Set Up the Environment

We recommend using a Python virtual environment to manage dependencies.

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
# venv\Scripts\activate
# On macOS and Linux:
source venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages using `pip`:

```bash
pip install -r requirements.txt
pip install -e .
```
Installing the package in editable mode (`-e .`) is important, as it ensures that the `daydream` module can be found by the test runner and the Flask CLI.

### 4. Configure Environment Variables

The application requires API keys for Google Cloud Firestore and Google Generative AI. You will need to set the following environment variables:

*   `FLASK_APP=daydream`
*   `FLASK_ENV=development`
*   `FLASK_SECRET_KEY`: A secret key for Flask sessions. You can generate one with `python -c 'import os; print(os.urandom(16))'`.
*   `FIREBASE_SERVICE_ACCOUNT_KEY`: The path to your Firebase service account JSON file.
*   `FIREBASE_WEB_API_KEY`: The Web API Key for your Firebase project. You can find this in your Firebase project settings under "General".
*   `GEMINI_API_KEY`: Your API key for the Google Generative AI service.

You can set these in your shell, or for a more permanent solution, create a `.env` file in the root of the project and use a tool like `python-dotenv` to load them.

## Running the Application

Once your environment is set up, you can run the application with the following command:

```bash
flask run
```

The application will be available at `http://127.0.0.1:5000`.

## Running Tests

To ensure that your changes haven't broken anything, please run the test suite before submitting a pull request.

```bash
python -m pytest
```

## Making Changes

1.  Create a new branch for your feature or bug fix:
    ```bash
    git checkout -b your-branch-name
    ```
2.  Make your changes and commit them with a clear and descriptive message.
3.  Push your branch to your fork:
    ```bash
    git push origin your-branch-name
    ```
4.  Open a pull request from your fork to the main repository.

## Code Style

This project follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code. We use `flake8` to enforce this. Before submitting your changes, please run `flake8` to check for any style issues:

```bash
flake8 .
```

Thank you for contributing to Daydream!