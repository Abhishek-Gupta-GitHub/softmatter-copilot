# Confocal Microscopy Copilot

An **AI-assisted confocal microscopy copilot** for simulating, analyzing, and explaining Brownian particle movies and soft‑matter experiments. It combines a digital twin of Brownian motion, classical image analysis, particle tracking, and LLM‑based agents to help experimentalists go from raw movies to quantitative physics and plain‑language reports. [page:1]

## Key Features

- Load or simulate confocal microscopy movies of Brownian particles. [page:1]
- Detect and track particles over time to build trajectories. [page:1]
- Estimate physical parameters such as diffusion coefficients and mean‑square displacement. [page:1]
- Use a configurable digital twin to compare experiment vs simulation. [page:1]
- Multi‑agent architecture (data I/O, detection/tracking, physics analysis, explanation). [page:1]
- Optional LLM‑based copilot to explain results, suggest next steps, and help with troubleshooting. [page:1]

---

## Repository Structure

The current repository is organized as: [page:1]

- `copilot/` – core multi‑agent logic (data loader, tracker, physics analyst, explainer). [page:1]
- `notebooks/` – Jupyter notebooks for demos and hackathon workflows. [page:1]
- `data/` – example datasets and synthetic movies (or download scripts). [page:1]
- `legacy/` – older scripts and experiments kept for reference. [page:1]
- `results/` – saved analysis outputs and figures. [page:1]
- `src/` – supporting source modules used by the UI and notebooks. [page:1]
- `ui_demo_final` – entry point script for the interactive demo UI. [page:1]
- `requirements.txt` – Python dependencies. [page:1]
- `LICENSE`, `README.md` – project metadata and documentation. [page:1]

---

## Installation

Clone the repository
git clone https://github.com/Abhishek-Gupta-GitHub/confocal_microscopy-copilot.git
cd confocal_microscopy-copilot

(Recommended) create and activate a virtual environment, then install dependencies
pip install -r requirements.txt

If `requirements.txt` is incomplete for your setup, install the main scientific stack manually (e.g. `numpy`, `scipy`, `matplotlib`, `pandas`, `trackpy`, `deeptrack`, and any UI / LLM dependencies you use). [page:1]

---

## How to run the UI demo (`ui_demo_final`)

The repo includes a ready‑to‑use UI demo that showcases the Confocal Microscopy Copilot end‑to‑end. [page:1]

### 1. Start the UI demo

From the repository root:


This will:

- Launch an interactive UI (for example a local web interface) in your browser.  
- Allow you to choose between loading experimental data or using built‑in example / synthetic movies.  
- Run the full pipeline: preprocessing → particle detection and tracking → physics analysis → optional LLM explanation.  

If a browser tab does not open automatically, copy the URL printed in the terminal (usually something like `http://127.0.0.1:7860`) and paste it into your browser.

### 2. What you can do in the UI

Typical interactions:

- **Select input data**  
  - Load your own confocal movie / stack from file, or  
  - Use provided example or synthetic datasets.

- **Tune analysis parameters**  
  - Adjust detection thresholds, minimum particle size, tracking search range, and frame selection.

- **Run tracking & analysis**  
  - Extract particle trajectories.  
  - Compute MSD curves and diffusion‑related quantities.  
  - Compare results with the internal Brownian **digital twin**.

- **Ask the copilot (if LLM enabled)**  
  - Get plain‑language explanations of plots and parameters.  
  - Ask what a given diffusion coefficient means or how to improve data quality.  

LLM support is optional; the UI still runs the classical image and tracking pipeline without an API key.

---

## Notebook Workflows

For transparent, step‑by‑step experiments, use the notebooks in the `notebooks/` folder. [page:1]

### 1. Open the notebooks

From the repo root:

jupyter lab

or
jupyter notebook


Then:

1. Navigate to the `notebooks/` folder. [page:1]  
2. Open the main hackathon notebook (for example: `confocal_copilot_demo.ipynb` or similarly named).  
3. Run the cells in order.

### 2. Typical notebook pipeline

The main notebook is organized into logical sections:

1. **Data loading / simulation**  
   - Load a confocal movie from `data/` or from your own file.  
   - Or generate synthetic Brownian movies using the digital twin.

2. **Particle detection and tracking**  
   - Detect particles frame‑by‑frame.  
   - Build trajectories with a tracking algorithm.  
   - Visualize tracks overlaid on the raw movie.

3. **Physics analysis**  
   - Compute mean‑square displacement (MSD) curves.  
   - Estimate diffusion coefficients and other physical parameters relevant for soft‑matter / colloidal systems.

4. **Copilot / LLM explanations (optional)**  
   - When configured, call the ChatExplainer‑type agent from within the notebook.  
   - Generate human‑readable summaries, method descriptions, and suggestions for parameter tuning or follow‑up experiments. [page:1]

### 3. When to use UI vs notebook

- Use the **UI demo** (`ui_demo_final`) for quick interactive exploration, hackathon judging, and non‑technical users.  
- Use the **notebooks** when you want:
  - Full transparency of each processing step.  
  - Custom plots or analysis.  
  - To integrate your own datasets and experimental protocols. [page:1]

---

## LLM / Copilot Integration

If LLM support is enabled: [page:1]

- Configure your API key and model name in `config.py` or via environment variables. [page:1]  
- The **ChatExplainer** (or equivalent agent) can:
  - Summarize analysis results.  
  - Explain physical meaning (e.g. diffusion coefficient, Brownian motion regimes).  
  - Suggest parameter changes or follow‑up experiments. [page:1]  

LLM integration is optional; the classical analysis pipeline works without it. [page:1]

---

## Use Cases

- Confocal Brownian motion experiments in soft matter and colloids. [page:1]  
- Educational demos for particle tracking and diffusion analysis. [page:1]  
- Rapid prototyping of microscopy copilot ideas for hackathons and lab projects. [page:1]

---

## Keywords

Confocal microscopy, Brownian motion, particle tracking, diffusion coefficient, soft matter physics, AI copilot, multi‑agent system, digital twin, image analysis pipeline, LLM‑driven microscopy assistant [page:1]

---

## License

This project is distributed under the MIT License (see `LICENSE` file for details). [page:1]

## Acknowledgements

- Built during a global microscopy / AI hackathon as a proof‑of‑concept **confocal physics copilot**. [page:1]  
- Inspired by existing work in confocal microscopy, particle tracking, and LLM‑based copilots for scientific workflows. [page:1]




From a terminal:

