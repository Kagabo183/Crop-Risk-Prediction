"""
Batch processor to enqueue NDVI processing tasks for all unprocessed TIFF files.
Useful after generating many test files or fetching real satellite imagery.
"""

import os
import sys
from pathlib import Path

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.tasks.process_tasks import process_image_task, scan_and_enqueue

def batch_enqueue_all():
    """Trigger scan_and_enqueue task to process all unprocessed TIFFs."""
    try:
        result = scan_and_enqueue.delay()
        print(f"Enqueued scan task: {result.id}")
        print("Monitor progress with:")
        print(f"  curl http://127.0.0.1:8000/api/v1/satellite-images/task/{result.id}")
        print("Or check worker logs:")
        print("  docker compose logs -f worker")
        return result
    except Exception as e:
        print(f"Error enqueueing scan: {e}")
        print("Make sure Redis/Celery broker is running (docker compose up or set REDIS_HOST=localhost)")
        return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Batch enqueue NDVI processing')
    parser.add_argument('--direct', action='store_true', help='Directly enqueue files without scanner')
    args = parser.parse_args()
    
    if args.direct:
        # Directly enqueue all TIFFs in data/sentinel2
        data_dir = Path("data/sentinel2")
        if not data_dir.exists():
            print(f"Directory {data_dir} not found")
            sys.exit(1)
        
        tifs = list(data_dir.glob("*.tif"))
        print(f"Found {len(tifs)} TIFF files. Enqueueing...")
        
        for tif in tifs:
            try:
                res = process_image_task.delay(str(tif))
                print(f"  Enqueued: {tif.name} -> task {res.id}")
            except Exception as e:
                print(f"  Failed {tif.name}: {e}")
    else:
        # Use scanner (recommended)
        batch_enqueue_all()
