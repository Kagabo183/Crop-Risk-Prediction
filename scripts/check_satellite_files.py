import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.data import SatelliteImage
from app.db.database import Base
from app.core.config import settings

# Adjust this if your settings are loaded differently
DATABASE_URL = settings.DATABASE_URL

def main():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    missing = []
    images = session.query(SatelliteImage).all()
    for img in images:
        # Remove leading slash for os.path.join
        rel_path = img.file_path.lstrip("/\\")
        abs_path = os.path.join(os.getcwd(), rel_path)
        if not os.path.exists(abs_path):
            missing.append((img.id, img.file_path))

    if missing:
        print("Missing files:")
        for img_id, path in missing:
            print(f"ID {img_id}: {path}")
    else:
        print("All satellite image files exist.")

if __name__ == "__main__":
    main()
