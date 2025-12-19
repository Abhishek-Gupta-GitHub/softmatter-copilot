# ui_demo.py
"""
Confocal Microscopy Copilot – demo UI

Three main flows:
1) Golden demo (example stack from digital twin).
2) Real-data analysis (upload or choose dataset).
3) Follow-up questions (reuse last JSON summary, no recompute).

Back-end agents:
- Digital twin (simulate stacks or load example_stack).
- Orchestrator (planner / Plan).
- DetectionTrackingWorker (trackpy-based detection + linking).
- PhysicsAnalyst (MSD, depth, bleaching, etc.).
- ChatExplainer (LLM- or template-based explanations).
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional

import numpy as np
import matplotlib.pyplot as plt
import gradio as gr

from copilot import config
from copilot.io_utils import (
    load_stack,
    load_metadata,
    save_stack,
    save_metadata,
    save_json,
    save_trajectories_csv,
)
from copilot.digital_twin import DigitalTwin
from copilot.orchestrator import Orchestrator
from copilot.detection_tracking import DetectionTrackingWorker
from copilot.physics_analysis import PhysicsAnalyst
from copilot.chat_explainer import ChatExplainer

# ---------------- Paths and singletons ---------------- #

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
RESULTS_DIR.mkdir(exist_ok=True, parents=True)

EXAMPLE_STACK_PATH = DATA_DIR / "example_stack.tif"
EXAMPLE_META_PATH = DATA_DIR / "example_stack_meta.json"
ANALYSIS_SUMMARY_PATH = DATA_DIR / "analysis_summary.json"
TRAJ_CSV_PATH = RESULTS_DIR / "trajectories_latest.csv"

_twin = DigitalTwin()
_orchestrator = Orchestrator()
_detector_tracker = DetectionTrackingWorker()
_physics_basic = PhysicsAnalyst()
_explainer = ChatExplainer()  # assumes default LLM client or template mode


# ---------------- Data helpers ---------------- #

def _ensure_example_stack() -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Ensure that example_stack.tif and metadata exist.
    If missing, simulate a small digital-twin dataset and save it.
    """
    DATA_DIR.mkdir(exist_ok=True, parents=True)

    if EXAMPLE_STACK_PATH.exists() and EXAMPLE_META_PATH.exists():
        stack = load_stack(EXAMPLE_STACK_PATH)
        meta = load_metadata(EXAMPLE_META_PATH)
        return stack, meta

    # Fallback: simulate a default twin dataset
    settings = config.DEFAULT_DIGITAL_TWIN_SETTINGS
    sim_result = _twin.simulate(settings)
    stack = sim_result["stack"]
    meta = sim_result["metadata"]

    save_stack(EXAMPLE_STACK_PATH, stack)
    save_metadata(EXAMPLE_META_PATH, meta)
    return stack, meta


def _crop_stack(stack: np.ndarray, max_frames: int) -> np.ndarray:
    """Crop a 4D (T, Z, Y, X) or 3D (Z, Y, X) stack along time."""
    if stack.ndim == 4:
        t = min(stack.shape[0], max_frames)
        return stack[:t]
    return stack


def _choose_dataset(
    dataset_choice: str,
    uploaded_file,
    max_frames: int,
) -> Tuple[np.ndarray, Dict[str, Any], str]:
    """
    Resolve dataset according to dropdown and uploaded file.

    Returns
    -------
    stack : np.ndarray
    metadata : dict
    dataset_label : str
    """
    # 1) Golden example from twin
    if dataset_choice == "example":
        stack, meta = _ensure_example_stack()
        stack = _crop_stack(stack, max_frames)
        return stack, meta, "example (digital twin)"

    # 2) Pre-registered folders (imagej_confocal, synthetic_gaussian, deeptrack_example)
    if dataset_choice in {"imagej_confocal", "synthetic_gaussian", "deeptrack_example"}:
        folder = DATA_DIR / dataset_choice
        stack_path = folder / "stack.tif"
        meta_path = folder / "metadata.json"
        if stack_path.exists() and meta_path.exists():
            stack = load_stack(stack_path)
            meta = load_metadata(meta_path)
            stack = _crop_stack(stack, max_frames)
            return stack, meta, dataset_choice

    # 3) User upload, if provided
    if uploaded_file is not None:
        from copilot.io_utils import load_stack as load_any_tiff

        stack = load_any_tiff(uploaded_file.name)
        meta = {
            "pixel_size_um": config.DEFAULT_PIXEL_SIZE_UM,
            "z_step_um": config.DEFAULT_Z_STEP_UM,
            "frame_interval_s": config.DEFAULT_FRAME_INTERVAL_S,
            "source": "uploaded",
        }
        stack = _crop_stack(stack, max_frames)
        return stack, meta, f"uploaded: {Path(uploaded_file.name).name}"

    # 4) Fallback: example
    stack, meta = _ensure_example_stack()
    stack = _crop_stack(stack, max_frames)
    return stack, meta, "example (fallback)"


def _choose_physics_engine(use_advanced: bool):
    """Hook for an optional advanced physics module."""
    # For now just return basic; can be extended if advanced module exists.
    return _physics_basic


# ---------------- Plot helpers ---------------- #

def _make_msd_plot(summary: Dict[str, Any]):
    msd = summary.get("msd")
    if not isinstance(msd, dict):
        return None

    taus = np.array(msd.get("taus", []) or msd.get("taus_s", []))
    vals = np.array(msd.get("values", []))
    if len(taus) == 0 or len(vals) == 0:
        return None

    fig, ax = plt.subplots()
    ax.loglog(taus, vals, "o-")
    ax.set_xlabel("lag time τ")
    ax.set_ylabel("MSD")
    ax.set_title("Mean-squared displacement")
    fig.tight_layout()
    return fig


def _make_depth_plot(summary: Dict[str, Any]):
    depth = summary.get("depth_profile") or summary.get("diagnostics", {}).get(
        "depth_profile_mean_intensity"
    )
    if depth is None:
        return None

    if isinstance(depth, dict):
        z = np.array(depth.get("z_index", []))
        mean_int = np.array(depth.get("mean_intensity", []))
    else:
        mean_int = np.array(depth)
        z = np.arange(len(mean_int))

    if len(z) == 0 or len(mean_int) == 0:
        return None

    fig, ax = plt.subplots()
    ax.plot(z, mean_int, "-o")
    ax.set_xlabel("z index")
    ax.set_ylabel("mean intensity")
    ax.set_title("Depth-dependent intensity")
    fig.tight_layout()
    return fig


# ---------------- Core pipeline ---------------- #

def _run_full_analysis(
    dataset_choice: str,
    uploaded_file,
    max_frames: int,
    analysis_prompt: str,
    use_advanced: bool,
) -> Tuple[str, str, str, str, Optional[object], Optional[object], Optional[str]]:
    """
    Full pipeline:
    data -> plan -> detection/tracking -> physics -> explanation.

    Returns
    -------
    explanation : str
    agent_log : str
    dataset_info : str
    summary_json_str : str
    msd_plot : matplotlib.Figure or None
    depth_plot : matplotlib.Figure or None
    traj_csv_path : str or None
    """
    # 0) Load / simulate stack
    stack, meta, label = _choose_dataset(dataset_choice, uploaded_file, max_frames)
    dataset_info = f"Dataset: {label}\nShape: {tuple(stack.shape)}"

    # Quick stats used by planner and logs
    mean_signal = float(stack.mean())
    std_signal = float(stack.std() + 1e-6)
    snr_est = mean_signal / std_signal
    quick_stats = {
        "snr_est": snr_est,
        "density_est": 200,
        "D_est": 0.2,
        "search_range_um": 1.5,
    }

    # 1) Planning
    plan = _orchestrator.make_plan(analysis_prompt, meta, quick_stats)

    # 2) Detection + tracking
    result = _detector_tracker.run(stack, plan)

    # Your worker returns a dict with keys like "trajectories" and "quality_metrics"
    if isinstance(result, dict):
        traj = result.get("trajectories")
        quality = result.get("quality_metrics", {})
    else:
        # fallback: tuple or other older API
        traj, quality = result, {}

    # Convert to DataFrame if necessary
    import pandas as pd
    if isinstance(traj, dict):
        traj_df = pd.DataFrame(traj)
    else:
        traj_df = traj

    if traj_df is None or len(traj_df) == 0:
        explanation = (
            "No reliable trajectories were found. "
            "Try fewer frames, lower density, or adjust detection parameters."
        )
        agent_log = "DetectionTrackingWorker: no features or tracks detected."
        summary = {
            "metadata": meta,
            "quick_stats": quick_stats,
            "plan": getattr(plan, "to_dict", lambda: {"plan_repr": str(plan)})(),
            "quality": quality,
            "flags_and_anomalies": ["no_trajectories"],
        }
        save_json(ANALYSIS_SUMMARY_PATH, summary)
        import json as _json
        return (
            explanation,
            agent_log,
            dataset_info,
            _json.dumps(summary, indent=2),
            None,
            None,
            None,
        )

    # Persist trajectories for download
    save_trajectories_csv(TRAJ_CSV_PATH, traj_df)


    # 3) Physics analysis
    physics_engine = _choose_physics_engine(use_advanced)
    summary = physics_engine.summarize(traj_df, stack, meta, plan)
    summary["metadata"] = meta
    summary["quick_stats"] = quick_stats
    if hasattr(plan, "to_dict"):
        summary["plan"] = plan.to_dict()
    else:
        summary["plan"] = {"plan_repr": str(plan)}
    summary["quality"] = quality

    save_json(ANALYSIS_SUMMARY_PATH, summary)

    # 4) Explanation
    explanation = _explainer.explain(analysis_prompt, summary)

    # 5) Agent log
    log_lines = []
    log_lines.append(
        f"Planner → pipeline_type: {getattr(plan, 'pipeline_type', 'NA')}"
    )
    log_lines.append(
        f"Planner → twin_needed: {getattr(plan, 'twin_needed', False)}"
    )
    log_lines.append(
        f"Planner → detection_params: {getattr(plan, 'detection_params', {})}"
    )
    log_lines.append(
        f"Planner → tracking_params: {getattr(plan, 'tracking_params', {})}"
    )
    log_lines.append(
        f"DetectionTracking → n_tracks: {quality.get('n_tracks', 'NA')}"
    )
    flags = summary.get("flags_and_anomalies", [])
    if flags:
        log_lines.append(f"Physics → flags: {flags}")
    agent_log = "\n".join(log_lines)

    # 6) Plots
    msd_plot = _make_msd_plot(summary)
    depth_plot = _make_depth_plot(summary)

    # 7) JSON string for advanced users
    import json
    summary_json_str = json.dumps(summary, indent=2)

    traj_path_str = str(TRAJ_CSV_PATH) if TRAJ_CSV_PATH.exists() else None

    return (
        explanation,
        agent_log,
        dataset_info,
        summary_json_str,
        msd_plot,
        depth_plot,
        traj_path_str,
    )


def _follow_up(question: str) -> str:
    """Follow-up using last saved JSON summary; no recompute."""
    if not ANALYSIS_SUMMARY_PATH.exists():
        return "No previous analysis summary found. Run an analysis first."

    import json
    summary = json.loads(ANALYSIS_SUMMARY_PATH.read_text())
    prompt = question if question.strip() else "Summarise the main findings."
    return _explainer.explain(prompt, summary)


# ---------------- Gradio UI ---------------- #

def build_ui() -> gr.Blocks:
    with gr.Blocks(title="Confocal Microscopy Copilot – Demo") as demo:
        gr.Markdown(
            "## Confocal Physics Copilot\n"
            "Digital-twin–assisted analysis of confocal particle-tracking data,\n"
            "with MSD, depth/bleaching diagnostics, and explainer agent.\n"
        )

        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 1. Dataset & twin")
                dataset_choice = gr.Dropdown(
                    choices=[
                        "example",
                        "imagej_confocal",
                        "synthetic_gaussian",
                        "deeptrack_example",
                        "uploaded",
                    ],
                    value="example",
                    label="Dataset",
                    info="Use 'example' for the golden demo (digital twin). "
                         "Other options require data/ subfolders or upload.",
                )

                uploaded_file = gr.File(
                    label="Upload TIFF / OME-TIFF (optional)",
                    file_types=[".tif", ".tiff"],
                )

                max_frames = gr.Slider(
                    1,
                    200,
                    value=60,
                    step=1,
                    label="Max frames to use (time cropping)",
                    info="Crop long movies for faster tracking.",
                )

                use_advanced = gr.Checkbox(
                    value=False,
                    label="Use advanced physics analysis (if available)",
                )

                gr.Markdown("### 2. Analysis prompt")
                prompt_templates = gr.Dropdown(
                    choices=[
                        "Analyze diffusion and comment on depth and bleaching.",
                        "Quantify subdiffusion and identify a reliable MSD fit window.",
                        "Focus on crowding and near-wall effects.",
                        "Custom",
                    ],
                    value="Analyze diffusion and comment on depth and bleaching.",
                    label="Suggested prompts",
                )

                analysis_prompt = gr.Textbox(
                    label="Analysis question",
                    lines=3,
                    value=(
                        "Compute MSD, estimate alpha and D, and explain whether the "
                        "motion is diffusive, subdiffusive, or confined. "
                        "Comment on depth-dependent intensity and bleaching."
                    ),
                )

                def _update_prompt(template: str):
                    if template == "Custom":
                        return gr.update()
                    return gr.update(value=template)

                prompt_templates.change(
                    _update_prompt,
                    inputs=prompt_templates,
                    outputs=analysis_prompt,
                )

                run_btn = gr.Button("▶ Run full analysis", variant="primary")

                gr.Markdown("### 3. Follow-up (no recompute)")
                followup_q = gr.Textbox(
                    label="Ask about the last run",
                    lines=2,
                    value="How reliable is the MSD at long times?",
                )
                followup_btn = gr.Button("Ask follow-up")

            with gr.Column(scale=2):
                gr.Markdown("### Outputs")
                explanation_out = gr.Textbox(
                    label="Copilot explanation",
                    lines=8,
                )
                agent_log_out = gr.Textbox(
                    label="Agent reasoning (debug view)",
                    lines=8,
                )
                dataset_info_out = gr.Textbox(
                    label="Dataset info",
                    lines=3,
                )
                summary_json_out = gr.Textbox(
                    label="Analysis summary (JSON)",
                    lines=10,
                )
                msd_plot_out = gr.Plot(label="MSD")
                depth_plot_out = gr.Plot(label="Depth profile")
                traj_download = gr.File(
                    label="Download trajectories (CSV)",
                    value=None,
                )

        # Wire main run button
        def _on_run(
            ds_choice,
            up_file,
            max_fr,
            prompt,
            use_adv,
        ):
            (
                explanation,
                agent_log,
                ds_info,
                summary_json_str,
                msd_fig,
                depth_fig,
                traj_path,
            ) = _run_full_analysis(
                dataset_choice=ds_choice,
                uploaded_file=up_file,
                max_frames=int(max_fr),
                analysis_prompt=prompt,
                use_advanced=use_adv,
            )

            traj_file = Path(traj_path) if traj_path else None
            return (
                explanation,
                agent_log,
                ds_info,
                summary_json_str,
                msd_fig,
                depth_fig,
                traj_file,
            )

        run_btn.click(
            _on_run,
            inputs=[dataset_choice, uploaded_file, max_frames, analysis_prompt, use_advanced],
            outputs=[
                explanation_out,
                agent_log_out,
                dataset_info_out,
                summary_json_out,
                msd_plot_out,
                depth_plot_out,
                traj_download,
            ],
        )

        # Follow-up
        followup_btn.click(
            _follow_up,
            inputs=[followup_q],
            outputs=[explanation_out],
        )

    return demo


if __name__ == "__main__":
    app = build_ui()
    app.launch()
