import rasterio
import numpy as np

# Example: Load a .tif file for model input
def load_tif(file_path):
    with rasterio.open(file_path) as src:
        image = src.read()  # numpy array: (bands, height, width)
        print(f"Loaded {file_path} with shape {image.shape}")
        return image

if __name__ == "__main__":
    # Replace with a real file path from your data/sentinel2/ directory
    example_path = "data/sentinel2/rgb_20251227_685.tif"
    image = load_tif(example_path)
    # Now you can pass 'image' to your model for prediction
