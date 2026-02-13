from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.database.session import get_db
from backend.database.models import Generation
from backend.services.history_service import get_history

router = APIRouter()

@router.get("/api/history")
async def api_get_history(
    limit: int = 50,
    offset: int = 0,
    category: Optional[str] = None,
    character_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get generation history."""
    query = db.query(Generation)
    
    if category:
        query = query.filter(Generation.category == category)
        
    if character_name:
        query = query.join(Generation.character).filter(Generation.character.name == character_name)
        
    results = query.order_by(Generation.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "items": [
            {
                "id": r.id,
                "image_path": r.image_path,
                "prompt": r.prompt,
                "settings": {
                    "steps": r.steps,
                    "cfg": r.cfg_scale,
                    "seed": r.seed,
                    "model": r.model_name
                },
                "created_at": r.created_at.isoformat(),
                "category": r.category
            }
            for r in results
        ],
        "total": query.count() # Note: simple count, optimize if slow
    }

@router.get("/api/history/{id}/remix")
async def api_get_remix(id: int, db: Session = Depends(get_db)):
    """Get specific generation settings for remixing."""
    gen = db.query(Generation).filter(Generation.id == id).first()
    if not gen:
        raise HTTPException(status_code=404, detail="Generation not found")
        
    return {
        "prompt": gen.prompt,
        "negative_prompt": gen.negative_prompt,
        "width": gen.width,
        "height": gen.height,
        "steps": gen.steps,
        "cfg_scale": gen.cfg_scale,
        "seed": gen.seed,
        "model_name": gen.model_name
    }
