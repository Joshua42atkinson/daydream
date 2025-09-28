
Daydream is a high-performance, local-first instructional design platform for creating storyfied, AI-driven gameducation. Built entirely in Rust, it runs completely offline on your own hardware, ensuring total privacy and data sovereignty.
This project is an open-source initiative to build a next-generation creative tool that empowers educators, trainers, and writers to build rich, interactive learning experiences without relying on cloud services.
The "Diamond Body" Vision
In an era of cloud-based AI, Daydream takes a different path. Our core philosophy is built on three pillars:
 * Sovereignty: Your data, your models, and your creative work never leave your machine. Daydream is designed to run entirely offline, giving you complete control and privacy.
 * Performance: By leveraging Rust and targeting modern AI-accelerated hardware, Daydream achieves performance that is impossible in typical web-based or Python-scripted environments. This allows for the use of powerful, large language models and complex multi-agent systems locally.
 * Accessibility: The entire platform is free, open-source, and built to be a single, distributable application. Our goal is to create a powerful tool that can be run by institutions and individuals who value privacy and performance, from a public school with a custom-built machine to a power user at home.
Key Features
 * AI-Powered Instructional Design: Go beyond static content. Build dynamic, narrative-driven learning modules where the story adapts to user choices and learning progress.
 * Local-First LLM Inference: The entire AI engine runs on your local machine. No API keys, no subscriptions, no data sent to third parties.
 * "Great Recycler" Multi-Agent System: A sophisticated, hierarchical agent system orchestrates the learning experience. A high-level strategic agent analyzes long-term progress while a crew of tactical agents manages quests, character development, and UI updates in real-time.
 * Modular Creator's Cockpit: A powerful yet intuitive desktop application where you can:
   * Design complex Quest Systems with triggers and objectives.[1]
   * Define and track custom Learning Objectives.[1]
   * Implement the "AI as a Mirror" Reflective Learning Loop for deeper metacognitive engagement.[1]
 * Cross-Platform Desktop App: Built with Tauri, Daydream is a lightweight, secure application that runs natively on Linux, macOS, and Windows.
Target Hardware Platform
Daydream v3 is engineered to harness the full potential of modern Accelerated Processing Units (APUs). The primary reference platform is the AMD Ryzen™ AI Max+ 395 ("Strix Halo") APU, a System-on-Chip that combines:
 * CPU: 16 high-performance "Zen 5" cores.
 * iGPU: A powerful 40 CU Radeon™ 8060S based on the RDNA™ 3.5 architecture.
 * NPU: A 50 TOPS XDNA™ 2 Neural Processing Unit for efficient, sustained AI workloads.
 * Unified Memory: Up to 128GB of high-speed LPDDR5X-8000 RAM, which can be dynamically allocated to the GPU, enabling the local execution of massive (70B+) language models.
This local-first "supercomputer" architecture allows Daydream to deliver a level of AI-driven complexity and responsiveness that is simply not possible with cloud-dependent services.
Technology Stack
This project is a pure Rust ecosystem, leveraging the best of the community for performance, safety, and modern development practices.
 * Application Framework:(https://tauri.app/) - For building a secure, lightweight, and cross-platform desktop application with a web-based frontend.
 * AI/ML Inference Engine: Candle - A minimalist, high-performance ML framework from Hugging Face, enabling us to run LLMs directly in Rust with CPU and GPU acceleration.
 * Multi-Agent Framework: AutoAgents - A cutting-edge Rust framework for building and coordinating multiple intelligent agents, forming the core of the "Great Recycler" system.
 * Game & State Engine:(https://bevyengine.org/) - Bevy's powerful, data-driven Entity-Component-System is used to manage the state of the instructional world, characters, and quests in a highly efficient manner.
Getting Started
This guide assumes you are on Ubuntu 24.04 LTS and are targeting the AMD "Strix Halo" platform.
1. Host System Preparation
To unlock the full unified memory capabilities of the hardware, you must configure the kernel's boot parameters.
# Edit the GRUB configuration file
sudo nano /etc/default/grub

# Find the line GRUB_CMDLINE_LINUX_DEFAULT and add the required parameters.
# The final line should look like this:
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amd_iommu=off amdgpu.gttsize=131072 ttm.pages_limit=33554432"

# Save the file, then update GRUB and reboot
sudo update-grub
sudo reboot

These settings allow the integrated GPU to address up to 128 GiB of system RAM, which is essential for running large models.
2. Install Dependencies
You will need the Rust toolchain, essential build tools, and Git.
# Install Rust via rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

# Install build essentials and Tauri prerequisites
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev

3. Clone and Build Daydream
# Clone the repository
git clone https://github.com/your-username/daydream.git
cd daydream

# Build the project in release mode
cargo build --release

# Run the application
cargo run --release

Roadmap
Daydream is an ambitious project under active development. Our high-level roadmap is structured as follows:
 * Phase 1: The Inference Core: Establish a high-performance, local-first inference engine using Candle and create the first autonomous NarrativeAgent.
 * Phase 2: The Great Recycler: Build the full multi-agent orchestration system, modularizing all application features (Quests, Learning Objectives, etc.) as subordinate agents.
 * Phase 3: The Creator's Cockpit: Deliver the complete, user-facing instructional design tool as a cross-platform desktop application using Tauri.
 * Phase 4: Diamond Body Optimization: Maximize performance by fully leveraging the target hardware's heterogeneous compute capabilities (iGPU and NPU acceleration).
Contributing
We are actively looking for contributors who are passionate about Rust, local-first AI, and the future of education. Whether you are a seasoned Rust developer, a UI/UX designer, or an instructional design expert, there is a place for you here.
Please read our CONTRIBUTING.md file for details on our code of conduct and the process for submitting pull requests.
License
This project is dual-licensed under the(LICENSE-MIT) and Apache License 2.0.

# Daydream Application State & Tool Manifest
# Version: 3.0.0-diamond-body
# This script defines the application's states and the tools available within each state.
# It is used by the Tauri frontend to render UI components and by the Great Recycler
# agent system to orchestrate complex, autonomous workflows.

version: 3.0.0-diamond-body
entry_point: MainMenu

states:
  #-----------------------------------------------------#
  # 1. Main Menu: The initial launch point of the application.
  #-----------------------------------------------------#
  MainMenu:
    description: "The primary entry point for the Daydream application. Provides options for project management and system configuration."
    ui_view: "views::main_menu"
    available_tools:
      - id: "project.create_new_module"
        description: "Initiates the creation of a new instructional design module from a template or a blank slate."
        agent_handler: "ProjectAgent"
        parameters:
          - name: "module_name"
            type: "string"
            description: "The title of the new instructional module."
          - name: "template"
            type: "enum"
            options:
            description: "The starting template for the module."
        on_success_transition_to: "CreatorCockpit"

      - id: "project.load_module"
        description: "Loads an existing instructional design module from the local filesystem for editing."
        agent_handler: "ProjectAgent"
        parameters:
          - name: "module_path"
            type: "path"
            description: "The file path to the module's root directory."
        on_success_transition_to: "CreatorCockpit"

      - id: "system.view_settings"
        description: "Navigates to the system-wide settings and configuration panel."
        agent_handler: "SystemAgent"
        parameters:
        on_success_transition_to: "Settings"

      - id: "system.view_diagnostics"
        description: "Accesses the hardware performance and diagnostics dashboard."
        agent_handler: "SystemAgent"
        parameters:
        on_success_transition_to: "SystemDiagnostics"

      - id: "system.exit"
        description: "Closes the Daydream application."
        agent_handler: "SystemAgent"
        parameters:
        on_success_transition_to: "TERMINATE"

  #-----------------------------------------------------#
  # 2. Creator Cockpit: The main workspace for an instructional designer.
  #-----------------------------------------------------#
  CreatorCockpit:
    description: "The central hub for managing and editing a loaded instructional module. Provides access to all creator tools."
    ui_view: "views::creator_cockpit"
    available_tools:
      - id: "editor.open_narrative_editor"
        description: "Opens the primary editor for writing and structuring the module's narrative, quests, and character interactions."
        agent_handler: "EditorAgent"
        parameters:
        on_success_transition_to: "ModuleEditor"

      - id: "editor.open_agent_config"
        description: "Opens the configuration panel for tuning the behavior of the AI agents used in the module."
        agent_handler: "EditorAgent"
        parameters:
        on_success_transition_to: "AgentConfiguration"

      - id: "project.save_module"
        description: "Saves all current changes to the instructional module."
        agent_handler: "ProjectAgent"
        parameters:
        on_success_transition_to: "CreatorCockpit" # Stays in the same state

      - id: "project.close_module"
        description: "Closes the current module and returns to the main menu."
        agent_handler: "ProjectAgent"
        parameters:
        on_success_transition_to: "MainMenu"

  #-----------------------------------------------------#
  # 3. Module Editor: The core instructional design interface.
  #    Integrates features from the Phoenix Project v2.0 design.[1]
  #-----------------------------------------------------#
  ModuleEditor:
    description: "A detailed editor for constructing the gameducation experience. Includes tools for quests, learning objectives, and reflection."
    ui_view: "views::module_editor"
    available_tools:
      - id: "module.edit_quest_graph"
        description: "Visually edit the quest structure, including objectives, triggers, and completion conditions."
        agent_handler: "QuestAgent"
        parameters:
          - name: "quest_id"
            type: "string"
            description: "The unique identifier for the quest to be edited."
        on_success_transition_to: "ModuleEditor"

      - id: "module.define_learning_objectives"
        description: "Create and manage the trackable learning objectives for the module (e.g., vocabulary, compliance items, historical facts)."
        agent_handler: "LearningObjectiveAgent"
        parameters:
          - name: "objective_id"
            type: "string"
            description: "The unique identifier for the learning objective."
          - name: "mastery_criteria"
            type: "struct"
            description: "Defines the conditions for mastering the objective (e.g., 'encountered: 3', 'applied_in_scenario: 1')."
        on_success_transition_to: "ModuleEditor"

      - id: "module.configure_reflection_loop"
        description: "Configure the 'AI as a Mirror' feature by setting triggers for Reflection Quests and authoring Socratic prompt templates."
        agent_handler: "ReflectionAgent"
        parameters:
          - name: "trigger_condition"
            type: "string"
            description: "The game state event that initiates a reflection (e.g., 'on_quest_complete:q1', 'on_player_choice:c5')."
          - name: "prompt_template"
            type: "string"
            description: "A template for the AI to generate a Socratic question, e.g., 'After that choice, what personal belief influenced your decision?'"
        on_success_transition_to: "ModuleEditor"

      - id: "editor.return_to_cockpit"
        description: "Returns to the main creator cockpit view."
        agent_handler: "EditorAgent"
        parameters:
        on_success_transition_to: "CreatorCockpit"

  #-----------------------------------------------------#
  # 4. Agent Configuration: Fine-tuning the AI's behavior.
  #-----------------------------------------------------#
  AgentConfiguration:
    description: "Interface for configuring the underlying AI models and agent personalities."
    ui_view: "views::agent_config"
    available_tools:
      - id: "agent.set_narrative_persona"
        description: "Select or define the personality of the primary storyteller AI."
        agent_handler: "NarrativeAgent"
        parameters:
          - name: "persona"
            type: "enum"
            options:
            description: "The AI personality to use for narrative generation."
        on_success_transition_to: "AgentConfiguration"

      - id: "agent.set_inference_parameters"
        description: "Adjust low-level inference parameters like temperature, top_p, and repetition penalty for the selected LLM."
        agent_handler: "InferenceAgent"
        parameters:
          - name: "temperature"
            type: "float"
            range: [0.0, 2.0]
          - name: "top_p"
            type: "float"
            range: [0.0, 1.0]
        on_success_transition_to: "AgentConfiguration"

      - id: "editor.return_to_cockpit"
        description: "Returns to the main creator cockpit view."
        agent_handler: "EditorAgent"
        parameters:
        on_success_transition_to: "CreatorCockpit"

  #-----------------------------------------------------#
  # 5. System Diagnostics: Hardware-specific tuning for the AMD APU.
  #-----------------------------------------------------#
  SystemDiagnostics:
    description: "Provides tools for monitoring and tuning the performance of the local-first AI hardware."
    ui_view: "views::diagnostics"
    available_tools:
      - id: "system.monitor_hardware_utilization"
        description: "Displays real-time usage graphs for the Zen 5 CPU cores, Radeon 8060S iGPU, and XDNA 2 NPU."
        agent_handler: "SystemAgent"
        parameters:
        on_success_transition_to: "SystemDiagnostics"

      - id: "system.set_vram_allocation"
        description: "Adjusts the amount of unified LPDDR5X RAM allocated as VRAM for the iGPU. Requires a restart."
        agent_handler: "SystemAgent"
        parameters:
          - name: "vram_gb"
            type: "integer"
            range: 
            description: "The amount of system RAM in gigabytes to allocate to the GPU."
        on_success_transition_to: "SystemDiagnostics"

      - id: "system.toggle_npu_offload"
        description: "Enables or disables experimental offloading of specific AI workloads to the 50 TOPS XDNA 2 NPU for power efficiency."
        agent_handler: "InferenceAgent"
        parameters:
          - name: "npu_enabled"
            type: "boolean"
        on_success_transition_to: "SystemDiagnostics"

      - id: "system.return_to_main_menu"
        description: "Returns to the main menu."
        agent_handler: "SystemAgent"
        parameters:
        on_success_transition_to: "MainMenu"

  #-----------------------------------------------------#
  # 6. Settings: Global application settings.
  #-----------------------------------------------------#
  Settings:
    description: "Global settings for the Daydream application, including model management and updates."
    ui_view: "views::settings"
    available_tools:
      - id: "inference.manage_local_models"
        description: "Download, update, or remove local LLM models (GGUF format) for offline use."
        agent_handler: "InferenceAgent"
        parameters:
          - name: "action"
            type: "enum"
            options: ["pull", "remove", "list"]
          - name: "model_name"
            type: "string"
            description: "The name of the model to act upon (e.g., 'llama3.1-8b-instruct.Q4_K_M.gguf')."
        on_success_transition_to: "Settings"

      - id: "system.check_for_updates"
        description: "Checks the open-source repository for new versions of the Daydream engine."
        agent_handler: "SystemAgent"
        parameters:
        on_success_transition_to: "Settings"

      - id: "system.return_to_main_menu"
        description: "Returns to the main menu."
        agent_handler: "SystemAgent"
        parameters:
        on_success_transition_to: "MainMenu"

