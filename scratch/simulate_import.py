import os
import sys

# Add backend to path
sys.path.insert(0, os.path.abspath('backend'))

from app.core.database import SessionLocal
from app.models.user import User
from app.services.job_import import process_import
import traceback

def test():
    db = SessionLocal()
    try:
        user = db.query(User).first()
        if not user:
            print("No user found")
            return
            
        print(f"Testing import for user {user.id}...")
        
        # Test URL import logic (same as api call, but direct)
        # Note: the API does db.add(job_import) before calling process_import but we can just use process_import directly for non-URL
        
        # Testing Description Import which uses process_import synchronously
        data = "Software Engineer at Google\nLocation: Mountain View\nSalary: $150k"
        import_record, jobs_data, errors, scrape_meta = process_import(
            db,
            user.id,
            "description",
            data
        )
        print("Success! Jobs:")
        print(jobs_data)
    except Exception as e:
        print("Exception caught:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test()
