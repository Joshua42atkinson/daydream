
Daydream is a high-performance, local-first instructional design platform for creating storyfied, AI-driven gameducation.
This project is an open-source initiative to build a next-generation creative tool that empowers educators, trainers, and writers to build rich, interactive learning experiences.

> **Note on Current Implementation:** This project is currently implemented as a Python-based web application using the Flask framework. The vision outlined in this README, including the Rust technology stack and the "Diamond Body" hardware target, represents the long-term architectural goal. The current codebase is the foundational prototype from which this vision will be realized.

## Getting Started with the Current Web Application

This guide will walk you through setting up and running the current Python and Flask-based web application.

### 1. Automated Setup

To simplify the setup process, a `setup.sh` script is provided to automate the installation of dependencies and the creation of the `.env` file.

```bash
./setup.sh
```

This script will:

*   Install all the required Python dependencies from `requirements.txt`.
*   Create a `.env` file from the `.env.example` template.

### 2. Manual Setup

If you prefer to set up the project manually, follow these steps:

*   **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
*   **Create the `.env` file:**
    ```bash
    cp .env.example .env
    ```

### 3. Configure Environment Variables

After running the setup script or performing a manual setup, you will need to configure your environment variables in the `.env` file. This file contains the necessary credentials for services like Firebase and the Gemini API.

### 4. Running the Application

Once you have configured your `.env` file, you can run the application in one of two modes:

*   **For development:**
    ```bash
    python run.py
    ```
*   **For production (recommended):**
    ```bash
    gunicorn --bind 0.0.0.0:8080 "run:app"
    ```

## The "Diamond Body" Vision

In an era of cloud-based AI, Daydream takes a different path. Our core philosophy is built on three pillars:

*   **Sovereignty:** Your data, your models, and your creative work never leave your machine. Daydream is designed to run entirely offline, giving you complete control and privacy.
*   **Performance:** By leveraging Rust and targeting modern AI-accelerated hardware, Daydream achieves performance that is impossible in typical web-based or Python-scripted environments. This allows for the use of powerful, large language models and complex multi-agent systems locally.
*   **Accessibility:** The entire platform is free, open-source, and built to be a single, distributable application. Our goal is to create a powerful tool that can be run by institutions and individuals who value privacy and performance, from a public school with a custom-built machine to a power user at home.

## Key Features

*   **AI-Powered Instructional Design:** Go beyond static content. Build dynamic, narrative-driven learning modules where the story adapts to user choices and learning progress.
*   **Local-First LLM Inference:** The entire AI engine runs on your local machine. No API keys, no subscriptions, no data sent to third parties.
*   **"Great Recycler" Multi-Agent System:** A sophisticated, hierarchical agent system orchestrates the learning experience. A high-level strategic agent analyzes long-term progress while a crew of tactical agents manages quests, character development, and UI updates in real-time.
*   **Modular Creator's Cockpit:** A powerful yet intuitive desktop application where you can:
    *   Design complex Quest Systems with triggers and objectives.[1]
    *   Define and track custom Learning Objectives.[1]
    *   Implement the "AI as a Mirror" Reflective Learning Loop for deeper metacognitive engagement.[1]
*   **Cross-Platform Desktop App:** Built with Tauri, Daydream is a lightweight, secure application that runs natively on Linux, macOS, and Windows.

## Target Hardware Platform

Daydream v3 is engineered to harness the full potential of modern Accelerated Processing Units (APUs). The primary reference platform is the AMD Ryzen™ AI Max+ 395 ("Strix Halo") APU, a System-on-Chip that combines:

*   **CPU:** 16 high-performance "Zen 5" cores.
*   **iGPU:** A powerful 40 CU Radeon™ 8060S based on the RDNA™ 3.5 architecture.
*   **NPU:** A 50 TOPS XDNA™ 2 Neural Processing Unit for efficient, sustained AI workloads.
*   **Unified Memory:** Up to 128GB of high-speed LPDDR5X-8000 RAM, which can be dynamically allocated to the GPU, enabling the local execution of massive (70B+) language models.

This local-first "supercomputer" architecture allows Daydream to deliver a level of AI-driven complexity and responsiveness that is simply not possible with cloud-dependent services.

## Technology Stack

This project is a pure Rust ecosystem, leveraging the best of the community for performance, safety, and modern development practices.

*   **Application Framework:**(https://tauri.app/) - For building a secure, lightweight, and cross-platform desktop application with a web-based frontend.
*   **AI/ML Inference Engine:** Candle - A minimalist, high-performance ML framework from Hugging Face, enabling us to run LLMs directly in Rust with CPU and GPU acceleration.
*   **Multi-Agent Framework:** AutoAgents - A cutting-edge Rust framework for building and coordinating multiple intelligent agents, forming the core of the "Great Recycler" system.
*   **Game & State Engine:**(https://bevyengine.org/) - Bevy's powerful, data-driven Entity-Component-System is used to manage the state of the instructional world, characters, and quests in a highly efficient manner.

## Getting Started

This guide assumes you are on Ubuntu 24.04 LTS and are targeting the AMD "Strix Halo" platform.

### 1. Host System Preparation

To unlock the full unified memory capabilities of the hardware, you must configure the kernel's boot parameters.

```bash
# Edit the GRUB configuration file
sudo nano /etc/default/grub

# Find the line GRUB_CMDLINE_LINUX_DEFAULT and add the required parameters.
# The final line should look like this:
GRUB_CMDLINE_LINUX_DEFAULT="quiet splash amd_iommu=off amdgpu.gttsize=131072 ttm.pages_limit=33554432"

# Save the file, then update GRUB and reboot
sudo update-grub
sudo reboot
```

These settings allow the integrated GPU to address up to 128 GiB of system RAM, which is essential for running large models.

### 2. Install Dependencies

You will need the Rust toolchain, essential build tools, and Git.

```bash
# Install Rust via rustup
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source "$HOME/.cargo/env"

# Install build essentials and Tauri prerequisites
sudo apt update
sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
```

### 3. Clone and Build Daydream

```bash
# Clone the repository
git clone https://github.com/your-username/daydream.git
cd daydream

# Build the project in release mode
cargo build --release

# Run the application
cargo run --release
```

## Roadmap

Daydream is an ambitious project under active development. Our high-level roadmap is structured as follows:

*   **Phase 1:** The Inference Core: Establish a high-performance, local-first inference engine using Candle and create the first autonomous NarrativeAgent.
*   **Phase 2:** The Great Recycler: Build the full multi-agent orchestration system, modularizing all application features (Quests, Learning Objectives, etc.) as subordinate agents.
*   **Phase 3:** The Creator's Cockpit: Deliver the complete, user-facing instructional design tool as a cross-platform desktop application using Tauri.
*   **Phase 4:** Diamond Body Optimization: Maximize performance by fully leveraging the target hardware's heterogeneous compute capabilities (iGPU and NPU acceleration).

## Contributing

We are actively looking for contributors who are passionate about Rust, local-first AI, and the future of education. Whether you are a seasoned Rust developer, a UI/UX designer, or an instructional design expert, there is a place for you here.

Please read our CONTRIBUTING.md file for details on our code of conduct and the process for submitting pull requests.

## License

This project is dual-licensed under the(LICENSE-MIT) and Apache License 2.0.

