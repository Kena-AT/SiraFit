from app.models.score import JobMatchScore
from app.core.database import engine, Base

Base.metadata.create_all(bind=engine)
print("Tables created.")
