import deeptrack as dt
import numpy as np
import pandas as pd

def detect_with_deeptrack2(image, voxel_size_um, diameter_um):
    cols = ["frame", "x", "y", "z", "intensity"]
    return pd.DataFrame(columns=cols)
