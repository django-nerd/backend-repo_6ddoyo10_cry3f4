"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# Example schemas (replace with your own):

class User(BaseModel):
    """
    Users collection schema
    Collection name: "user" (lowercase of class name)
    """
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product" (lowercase of class name)
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")

# Add your own schemas here:
# --------------------------------------------------

class Model(BaseModel):
    """
    Model/Hostess profiles
    Collection: "model"
    """
    name: str = Field(..., description="Full name")
    city: str = Field(..., description="Home city")
    bio: Optional[str] = Field(None, description="Short bio")
    experience_years: Optional[int] = Field(0, ge=0, le=50)
    hourly_rate: Optional[float] = Field(None, ge=0)
    skills: List[str] = Field(default_factory=list, description="Key skills/tags")
    photos: List[str] = Field(default_factory=list, description="Image URLs")
    instagram: Optional[str] = Field(None, description="Instagram handle or link")
    phone: Optional[str] = Field(None, description="Contact phone (optional)")

class Club(BaseModel):
    """
    Club/venue profiles
    Collection: "club"
    """
    name: str
    city: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None

class Gig(BaseModel):
    """
    Club night / temporary job posting
    Collection: "gig"
    """
    title: str
    club_name: str
    city: str
    date: str = Field(..., description="ISO date or friendly date string")
    location: Optional[str] = None
    pay: Optional[str] = Field(None, description="Compensation details e.g. $50/hr + tips")
    dress_code: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)
    spots: int = Field(1, ge=1, description="Number of models needed")
    notes: Optional[str] = None

class Application(BaseModel):
    """
    Applications from models to gigs
    Collection: "application"
    """
    gig_id: str
    model_id: str
    message: Optional[str] = None
    status: str = Field("pending", description="pending|approved|rejected")
    applied_at: Optional[datetime] = None

# Note: The Flames database viewer will automatically:
# 1. Read these schemas from GET /schema endpoint
# 2. Use them for document validation when creating/editing
# 3. Handle all database operations (CRUD) directly
# 4. You don't need to create any database endpoints!
