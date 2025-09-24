# Open WebUI Integration Guide

This guide explains how to configure Open WebUI to use the Daydream game engine as a backend. This will allow you to use the Open WebUI interface to interact with the game's AI, "The Great Recycler".

## Prerequisites

*   You have a running instance of the Daydream application.
*   You have a running instance of Open WebUI.

## Configuration Steps

1.  **Log in to Open WebUI as an administrator.**

2.  **Navigate to the "Admin" settings page.**

3.  **Go to the "Models" section.**

4.  **Add a new model with the following configuration:**

    *   **Model Name:** `The Great Recycler` (or any name you prefer)
    *   **Base URL:** `http://<your-daydream-app-host>:<port>/api` (e.g., `http://127.0.0.1:8080/api`)
    *   **API Key:** This is not required for the current implementation, but you can add a placeholder if needed.
    *   **Model:** `daydream/chat` (This should match the route we created in the API)

5.  **Save the new model.**

6.  **Go back to the main chat interface and select "The Great Recycler" from the model dropdown.**

You should now be able to chat with the Daydream application through the Open WebUI interface.

## How it Works

When you send a message in the Open WebUI chat, it will make a POST request to the `/api/chat` endpoint of the Daydream application. The Daydream application will then process the message, get a response from the AI, and send it back to the Open WebUI interface.

## Troubleshooting

*   **404 Not Found:** Ensure that the Base URL and Model name are correct in the Open WebUI settings.
*   **Authentication Errors:** The `/api/chat` endpoint requires a logged-in user. In a real-world scenario, you would need to handle authentication between Open WebUI and the Daydream application. This could be done using API keys or another authentication mechanism. For now, you will need to be logged into the Daydream application in the same browser session.
*   **Ethical Gateway Blocks:** If your message is blocked by the ethical gateway, you will see a message indicating the reason.