# Daydream Design Document

## 1. Introduction

Daydream is a narrative-driven game engine built with Flask. It is designed for educational purposes, allowing users to create and play through stories that incorporate vocabulary and critical thinking exercises. The application leverages Google's Generative AI to create dynamic and interactive story content.

## 2. Architecture

The application follows a modular, blueprint-based architecture, which is common for Flask projects. This is similar to a Model-View-Controller (MVC) pattern:

*   **Model**: The data layer is managed by Google Cloud Firestore. Data models are not defined by a traditional ORM but are represented by the structure of documents within Firestore collections. Key data includes user profiles, character sheets, and game state.
*   **View**: The presentation layer is handled by Jinja2 templates. These templates render the HTML pages that the user interacts with.
*   **Controller**: The application logic resides within the Flask route functions defined in various blueprints. These functions handle user requests, interact with the database and AI services, and render the appropriate templates.

## 3. Core Components (Blueprints)

The application is divided into several Flask blueprints, each responsible for a specific area of functionality:

*   **`auth`**: Manages user authentication (login, logout, registration).
*   **`character`**: Handles character creation, management, and viewing character templates.
*   **`game`**: The core game loop, processing user input and generating story content.
*   **`journal`**: Allows users to view their character's journal, which includes summaries of past events.
*   **`profile`**: The user's main dashboard, where they can see their characters and start a game.
*   **`eoc`**: End-of-chapter functionality, including vocabulary review.
*   **`vocabulary`**: Manages and displays vocabulary words.

## 4. Data Models (Firestore)

The primary data is stored in Google Cloud Firestore. The main collection is `characters`.

### `characters` collection:
Each document in this collection represents a character and has a unique ID. The document contains fields such as:
*   `id`: Unique character ID.
*   `user_id`: The ID of the user who owns the character.
*   `name`: The character's name.
*   `race_name`, `class_name`, `philosophy_name`: Core character attributes.
*   `abilities`: A list of character abilities.
*   `inventory`: A list of items the character possesses.
*   `current_location`: The character's current location in the game world.
*   `fate_points`: A resource for players.
*   `conversation`: A log of the conversation with the AI.
*   `quest_flags`: A dictionary of flags to track quest progress.
*   ...and other game state variables.

## 5. Data Flow

A typical game session follows this flow:

1.  **User Input**: The user submits an action or dialogue through a form on the game page.
2.  **Request Handling**: The corresponding route function in the `game` blueprint receives the request.
3.  **State Retrieval**: The character's current state is loaded from the Firestore database.
4.  **AI Interaction**: The user's input, along with the current game context (location, inventory, quests), is sent to the Google Generative AI model.
5.  **AI Response**: The AI returns a response containing the next part of the story, dialogue, or game state changes.
6.  **State Update**: The application updates the character's data in Firestore with the new information from the AI's response.
7.  **Render Response**: The new game state is rendered using a Jinja2 template and sent back to the user's browser.

## 6. External Services

*   **Google Cloud Firestore**: Used as the primary NoSQL database for storing all application data.
*   **Google Generative AI (Gemini)**: The core engine for generating dynamic story content and interacting with the player.