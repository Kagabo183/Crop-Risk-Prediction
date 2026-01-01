"""
Batch script to load all satellite images from the database and process them with your model.
Update the 'process_image' function to use your actual ML model.
"""
from app.db.database import SessionLocal
from app.models.data import SatelliteImage
import rasterio

def process_image(image_array, img_record):
    # TODO: Replace this with your actual model prediction logic
    # Example: return model.predict(image_array)
    print(f"Processing image {img_record.file_path} (id={img_record.id}) with shape {image_array.shape}")
    return None  # Replace with actual prediction

def main():
    session = SessionLocal()
    images = session.query(SatelliteImage).all()
    for img in images:
        file_path = img.file_path.lstrip("/\\")
        try:
            with rasterio.open(file_path) as src:
                image = src.read()
                result = process_image(image, img)
                # Optionally, save result to DB or file here
        except Exception as e:
            print(f"Could not open {file_path}: {e}")

if __name__ == "__main__":
    main()
