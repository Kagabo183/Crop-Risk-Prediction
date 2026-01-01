import sys
import rasterio
import matplotlib.pyplot as plt


def inspect_tif(file_path):
    print(f"Inspecting: {file_path}\n")
    with rasterio.open(file_path) as src:
        print("Metadata:")
        print(f"  Width: {src.width}")
        print(f"  Height: {src.height}")
        print(f"  Bands: {src.count}")
        print(f"  CRS: {src.crs}")
        print(f"  Bounds: {src.bounds}")
        print(f"  Dtype: {src.dtypes}")
        print(f"  Driver: {src.driver}")
        print(f"  Description: {src.descriptions}")
        print(f"  Transform: {src.transform}\n")

        # Read the first band for visualization
        band1 = src.read(1)
        plt.figure(figsize=(8, 8))
        plt.title(f"Preview: {file_path}")
        plt.imshow(band1, cmap='gray')
        plt.colorbar(label='Pixel Value')
        plt.axis('off')
        plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect_tif_file.py <path_to_tif_file>")
        sys.exit(1)
    inspect_tif(sys.argv[1])
