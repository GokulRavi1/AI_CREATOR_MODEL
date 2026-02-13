from sqlalchemy.orm import Session
from backend.database.models import Generation, Character
from backend.database.session import SessionLocal
import os

def log_generation(
    image_path: str,
    character_name: str,
    prompt: str,
    negative_prompt: str,
    settings: dict,
    category: str = "face_discovery",
    embedding: list = None
):
    """Log a generated image to the database."""
    db = SessionLocal()
    try:
        # 1. Find or create character
        # Note: In a real app, character should definitely exist. 
        # But for robustness, we handle potential missing cases or just query by name.
        char = db.query(Character).filter(Character.name == character_name).first()
        if not char:
            # Create if missing (auto-recovery)
            char = Character(name=character_name, trigger_word="ohm_person")
            db.add(char)
            db.commit()
            db.refresh(char)
            
        # 2. Create Generation record
        generation = Generation(
            character_id=char.id,
            image_path=image_path,
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=settings.get("seed", -1),
            steps=settings.get("steps", 20),
            cfg_scale=settings.get("cfg_scale", 7.0),
            width=settings.get("width", 512),
            height=settings.get("height", 512),
            model_name=settings.get("model", "unknown"),
            category=category,
            embedding=embedding
        )
        
        db.add(generation)
        db.commit()
        db.refresh(generation)
        return generation
    except Exception as e:
        print(f"Error logging generation: {e}")
        db.rollback()
    finally:
        db.close()

def get_history(limit: int = 50, offset: int = 0, category: str = None):
    """Get recent generations."""
    db = SessionLocal()
    try:
        query = db.query(Generation)
        if category:
            query = query.filter(Generation.category == category)
            
        return query.order_by(Generation.created_at.desc()).limit(limit).offset(offset).all()
    finally:
        db.close()
