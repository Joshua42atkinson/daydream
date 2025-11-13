# Daydream Development Roadmap

This document outlines a high-level roadmap for the future development of the Daydream platform, based on the "Architecture of Enjoyment" document and the proposed technical enhancements.

## Phase 1: The Foundation (Python/Flask)

**Goal:** Implement the core gamified learning loop within the existing Python/Flask framework.

**Deliverables:**

*   **Persona Engine:** Implement the Archetype, Dilemma, and Choice models, and the Persona Quiz and Reveal routes.
*   **VaaM Loop:** Implement the VocabularyWord and Puzzle models, and the VaaM loop routes and services.
*   **LitRPG Character Sheet:** Implement the CharacterSheet and SkillTree models, and the Character Sheet routes and services.
*   **"AI as a Mirror" Service:** Create a basic implementation of the "AI as a Mirror" service, integrated with a large language model.
*   **Simplified Creator's Sandbox:** Develop a web-based, node-based editor for creating branching narratives, with a simple "triggers and states" system and a media library.

## Phase 2: The Rust Transition

**Goal:** Begin the transition to a high-performance, local-first desktop application built with Rust.

**Deliverables:**

*   **Inference Core:** Establish a high-performance, local-first inference engine using Candle.
*   **NarrativeAgent:** Create the first autonomous NarrativeAgent.
*   **Tauri Application Shell:** Develop the basic Tauri application shell for the desktop application.
*   **Port of the Persona Engine to Rust:** Port the Persona Engine from Python/Flask to Rust.

## Phase 3: The Great Recycler

**Goal:** Build the full multi-agent orchestration system.

**Deliverables:**

*   **Multi-Agent Framework:** Integrate the AutoAgents framework for multi-agent orchestration.
*   **Modularization of Features:** Modularize all application features (Quests, Learning Objectives, etc.) as subordinate agents.
*   **Port of the VaaM Loop to Rust:** Port the VaaM loop from Python/Flask to Rust.

## Phase 4: The Creator's Cockpit

**Goal:** Deliver the complete, user-facing instructional design tool as a cross-platform desktop application.

**Deliverables:**

*   **Full Creator's Cockpit:** Implement the full "Twine + Storyline + Genially" synthesis for the Creator's Cockpit.
*   **Diamond Body Optimization:** Maximize performance by fully leveraging the target hardware's heterogeneous compute capabilities (iGPU and NPU acceleration).
*   **Full Port to Rust:** Complete the port of the entire application to Rust.
