from softmatter_copilot.io import load_tiff_stack
from softmatter_copilot.detection import detect_with_deeptrack2
from softmatter_copilot.tracking import track_with_trackpy
from softmatter_copilot.analysis import compute_msd

def main():
    path = "examples/example_stack.tif"
    voxel_size_um = (0.2, 0.2, 0.5)
    diameter_um = 2.0
    frame_interval = 1.0

    data = load_tiff_stack(path)
    detections = detect_with_deeptrack2(data, voxel_size_um, diameter_um)
    tracks = track_with_trackpy(detections, search_range=5)
    msd = compute_msd(tracks, frame_interval)
    print(msd.head())

if __name__ == "__main__":
    main()
