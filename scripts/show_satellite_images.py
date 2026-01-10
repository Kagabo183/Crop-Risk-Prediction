"""
Script to visualize Sentinel-2 satellite images from the project
Shows what the NDVI/EVI/RGB images look like
"""
import os
import sys
import matplotlib.pyplot as plt
import numpy as np

try:
    import rasterio
except ImportError:
    print("Installing rasterio...")
    os.system(f"{sys.executable} -m pip install rasterio")
    import rasterio

# Directory with satellite images
TIF_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sentinel2")

def show_sample_images():
    """Display sample NDVI, EVI, and RGB images"""
    
    # Get sample files
    files = os.listdir(TIF_DIR)
    ndvi_files = [f for f in files if f.startswith('ndvi_')][:1]
    evi_files = [f for f in files if f.startswith('evi_')][:1]
    rgb_files = [f for f in files if f.startswith('rgb_')][:1]
    
    samples = []
    for f in ndvi_files + evi_files + rgb_files:
        samples.append(os.path.join(TIF_DIR, f))
    
    if not samples:
        print("No satellite images found!")
        return
    
    print(f"Found {len(files)} total satellite images")
    print(f"  - NDVI images: {len([f for f in files if f.startswith('ndvi_')])}")
    print(f"  - EVI images: {len([f for f in files if f.startswith('evi_')])}")
    print(f"  - RGB images: {len([f for f in files if f.startswith('rgb_')])}")
    print()
    
    # Create figure
    fig, axes = plt.subplots(1, len(samples), figsize=(5*len(samples), 5))
    if len(samples) == 1:
        axes = [axes]
    
    for ax, path in zip(axes, samples):
        filename = os.path.basename(path)
        
        with rasterio.open(path) as src:
            data = src.read(1)  # Read first band
            
            # Get georeferencing info
            bounds = src.bounds
            crs = src.crs
            transform = src.transform
            
            print(f"📷 {filename}")
            print(f"   Size: {src.width}x{src.height} pixels")
            print(f"   CRS: {crs}")
            print(f"   Bounds: {bounds}")
            print(f"   Geographic extent:")
            print(f"     - Lat: {bounds.bottom:.4f} to {bounds.top:.4f}")
            print(f"     - Lng: {bounds.left:.4f} to {bounds.right:.4f}")
            print(f"   Data range: {data.min():.3f} to {data.max():.3f}")
            print()
            
            # Plot
            if 'ndvi' in filename.lower() or 'evi' in filename.lower():
                # Vegetation index - use green colormap
                im = ax.imshow(data, cmap='RdYlGn', vmin=-0.2, vmax=0.9)
                plt.colorbar(im, ax=ax, label='Index Value')
            else:
                # RGB - grayscale for single band
                im = ax.imshow(data, cmap='gray')
            
            ax.set_title(f"{filename}\n{src.width}x{src.height} px")
            ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('satellite_preview.png', dpi=150, bbox_inches='tight')
    print("✅ Saved preview to: satellite_preview.png")
    plt.show()

if __name__ == "__main__":
    show_sample_images()
