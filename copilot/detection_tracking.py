# copilot/detection_tracking.py

import pandas as pd
import numpy as np
import trackpy as tp

class DetectionTrackingWorker:
    def __init__(self):
        pass

    def _project_to_2d(self, stack_3d):
        # stack_3d: (T, Z, Y, X)
        return stack_3d.max(axis=1)  # (T, Y, X)

    def run(self, stack_3d, plan):
        frames_2d = self._project_to_2d(stack_3d)

        # Loosen parameters a bit for synthetic data
        diameter = int(2 * plan.detection_params_initial["max_sigma"] + 1)
        minmass = plan.detection_params_initial["minmass"]

        f_list = []
        for t, frame in enumerate(frames_2d):
            f = tp.locate(
                frame,
                diameter=diameter,
                minmass=minmass,
            )
            if len(f) == 0:
                continue
            f["frame"] = t
            f_list.append(f)

        print("Frames with detections:", len(f_list))

        # NEW: guard against no detections
        if not f_list:
            print("No features detected in any frame; returning empty trajectories.")
            empty = pd.DataFrame(columns=["x", "y", "frame", "particle"])
            return {
                "trajectories": empty,
                "quality_metrics": {
                    "n_tracks": 0,
                    "track_length_hist": {},
                    "detections_per_frame": {},
                },
                "used_params": {
                    "detection": plan.detection_params_initial,
                    "tracking": plan.tracking_params_initial,
                },
            }

        features = pd.concat(f_list, ignore_index=True)

        # NEW EXTRA GUARD
        if features.empty:
            print("Features DataFrame is empty; skipping linking.")
            empty = pd.DataFrame(columns=["x", "y", "frame", "particle"])
            return {
                "trajectories": empty,
                "quality_metrics": {
                    "n_tracks": 0,
                    "track_length_hist": {},
                    "detections_per_frame": {},
                },
                "used_params": {
                    "detection": plan.detection_params_initial,
                    "tracking": plan.tracking_params_initial,
                },
            }


        trajectories = tp.link_df(
            features,
            search_range=plan.tracking_params_initial["search_range"],
            memory=plan.tracking_params_initial["memory"],
        )

        n_tracks = trajectories["particle"].nunique()
        track_lengths = trajectories.groupby("particle")["frame"].count()
        track_length_hist = track_lengths.value_counts().to_dict()
        detections_per_frame = features.groupby("frame").size().to_dict()

        return {
            "trajectories": trajectories,
            "quality_metrics": {
                "n_tracks": int(n_tracks),
                "track_length_hist": track_length_hist,
                "detections_per_frame": detections_per_frame,
            },
            "used_params": {
                "detection": plan.detection_params_initial,
                "tracking": plan.tracking_params_initial,
            },
        }
