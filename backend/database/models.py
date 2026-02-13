from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean, JSON, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .session import Base

class Character(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text)
    trigger_word = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    generations = relationship("Generation", back_populates="character")

class Generation(Base):
    __tablename__ = "generations"

    id = Column(Integer, primary_key=True, index=True)
    character_id = Column(Integer, ForeignKey("characters.id"))
    
    # File info
    image_path = Column(String, nullable=False)
    
    # Generation Settings
    prompt = Column(Text)
    negative_prompt = Column(Text)
    seed = Column(BigInteger) # Use BigInteger for seeds
    steps = Column(Integer)
    cfg_scale = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    model_name = Column(String)
    
    # Metadata
    category = Column(String)  # 'face_discovery', 'body_consistency', 'dataset'
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Intelligence (Embeddings)
    # 768 dimensions is standard for CLIP/OpenAI embeddings (check your model)
    # We'll use 512 for now if using a smaller local model, or 768. 
    # Let's assume standard CLIP ViT-L/14 is 768.
    embedding = Column(Vector(768)) 
    
    character = relationship("Character", back_populates="generations")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
