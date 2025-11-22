# server.py
from fastapi import FastAPI, HTTPException, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from bson import ObjectId
from datetime import datetime
import os
from enum import Enum

# Pydantic models
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class SizeEnum(str, Enum):
    size_5 = "5"
    size_5_5 = "5.5"
    size_6 = "6"
    size_6_5 = "6.5"
    size_7 = "7"
    size_7_5 = "7.5"
    size_8 = "8"
    size_8_5 = "8.5"
    size_9 = "9"
    size_9_5 = "9.5"
    size_10 = "10"
    size_10_5 = "10.5"
    size_11 = "11"
    size_11_5 = "11.5"
    size_12 = "12"
    size_13 = "13"
    size_14 = "14"

class CategoryEnum(str, Enum):
    sneakers = "sneakers"
    boots = "boots"
    dress_shoes = "dress_shoes"
    sandals = "sandals"
    athletic = "athletic"
    casual = "casual"

class GenderEnum(str, Enum):
    men = "men"
    women = "women"
    unisex = "unisex"

class ShoeSize(BaseModel):
    size: SizeEnum
    quantity: int = Field(ge=0)

class Shoe(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    name: str = Field(..., min_length=1, max_length=100)
    brand: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., max_length=1000)
    price: float = Field(..., gt=0)
    category: CategoryEnum
    gender: GenderEnum
    color: str = Field(..., min_length=1, max_length=30)
    material: str = Field(..., min_length=1, max_length=50)
    sizes: List[ShoeSize]
    image_urls: List[str] = Field(default_factory=list)
    is_featured: bool = False
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ShoeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    brand: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., max_length=1000)
    price: float = Field(..., gt=0)
    category: CategoryEnum
    gender: GenderEnum
    color: str = Field(..., min_length=1, max_length=30)
    material: str = Field(..., min_length=1, max_length=50)
    sizes: List[ShoeSize]
    image_urls: List[str] = Field(default_factory=list)
    is_featured: bool = False

class ShoeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    brand: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[CategoryEnum] = None
    gender: Optional[GenderEnum] = None
    color: Optional[str] = Field(None, min_length=1, max_length=30)
    material: Optional[str] = Field(None, min_length=1, max_length=50)
    sizes: Optional[List[ShoeSize]] = None
    image_urls: Optional[List[str]] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = None

class CartItem(BaseModel):
    shoe_id: PyObjectId
    size: SizeEnum
    quantity: int = Field(..., ge=1)

class Cart(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = Field(..., min_length=1)
    items: List[CartItem]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"

class OrderItem(BaseModel):
    shoe_id: PyObjectId
    shoe_name: str
    shoe_brand: str
    size: SizeEnum
    quantity: int = Field(..., ge=1)
    price: float = Field(..., gt=0)

class ShippingAddress(BaseModel):
    street: str = Field(..., min_length=1, max_length=100)
    city: str = Field(..., min_length=1, max_length=50)
    state: str = Field(..., min_length=1, max_length=50)
    zip_code: str = Field(..., min_length=5, max_length=10)
    country: str = Field(..., min_length=1, max_length=50)

class Order(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    user_id: str = Field(..., min_length=1)
    items: List[OrderItem]
    total_amount: float = Field(..., gt=0)
    status: OrderStatus = OrderStatus.pending
    shipping_address: ShippingAddress
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class OrderCreate(BaseModel):
    user_id: str = Field(..., min_length=1)
    items: List[CartItem]
    shipping_address: ShippingAddress

# Initialize FastAPI app
app = FastAPI(
    title="Shoe Store API",
    description="A RESTful API for an online shoe store",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "shoe_store")

client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]
shoes_collection = database["shoes"]
carts_collection = database["carts"]
orders_collection = database["orders"]

# Helper functions
async def get_shoe_by_id(shoe_id: str) -> Optional[dict]:
    """Get a shoe by ID from the database."""
    if not ObjectId.is_valid(shoe_id):
        return None
    return await shoes_collection.find_one({"_id": ObjectId(shoe_id), "is_active": True})

# Shoe routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Shoe Store API"}

@app.get("/shoes", response_model=List[Shoe])
async def get_shoes(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[CategoryEnum] = None,
    gender: Optional[GenderEnum] = None,
    brand: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    featured: Optional[bool] = None
):
    """Get all shoes with optional filtering."""
    filter_dict = {"is_active": True}
    
    if category:
        filter_dict["category"] = category
    if gender:
        filter_dict["gender"] = gender
    if brand:
        filter_dict["brand"] = {"$regex": brand, "$options": "i"}
    if min_price is not None and max_price is not None:
        filter_dict["price"] = {"$gte": min_price, "$lte": max_price}
    elif min_price is not None:
        filter_dict["price"] = {"$gte": min_price}
    elif max_price is not None:
        filter_dict["price"] = {"$lte": max_price}
    if featured is not None:
        filter_dict["is_featured"] = featured
    
    cursor = shoes_collection.find(filter_dict).skip(skip).limit(limit)
    shoes = await cursor.to_list(length=limit)
    return shoes

@app.get("/shoes/{shoe_id}", response_model=Shoe)
async def get_shoe(shoe_id: str = Path(..., description="The ID of the shoe")):
    """Get a specific shoe by ID."""
    shoe = await get_shoe_by_id(shoe_id)
    if not shoe:
        raise HTTPException(status_code=404, detail="Shoe not found")
    return shoe

@app.post("/shoes", response_model=Shoe, status_code=201)
async def create_shoe(shoe: ShoeCreate):
    """Create a new shoe."""
    shoe_dict = shoe.dict()
    shoe_dict["created_at"] = datetime.utcnow()
    shoe_dict["updated_at"] = datetime.utcnow()
    
    result = await shoes_collection.insert_one(shoe_dict)
    created_shoe = await shoes_collection.find_one({"_id": result.inserted_id})
    return created_shoe

@app.put("/shoes/{shoe_id}", response_model=Shoe)
async def update_shoe(
    shoe_update: ShoeUpdate,
    shoe_id: str = Path(..., description="The ID of the shoe")
):
    """Update a specific shoe."""
    if not ObjectId.is_valid(shoe_id):
        raise HTTPException(status_code=400, detail="Invalid shoe ID")
    
    update_dict = {k: v for k, v in shoe_update.dict().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await shoes_collection.update_one(
        {"_id": ObjectId(shoe_id)},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Shoe not found")
    
    updated_shoe = await shoes_collection.find_one({"_id": ObjectId(shoe_id)})
    return updated_shoe

@app.delete("/shoes/{shoe_id}")
async def delete_shoe(shoe_id: str = Path(..., description="The ID of the shoe")):
    """Soft delete a shoe (mark as inactive)."""
    if not ObjectId.is_valid(shoe_id):
        raise HTTPException(status_code=400, detail="Invalid shoe ID")
    
    result = await shoes_collection.update_one(
        {"_id": ObjectId(shoe_id)},
        {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Shoe not found")
    
    return {"message": "Shoe deleted successfully"}

# Cart routes
@app.get("/cart/{user_id}", response_model=Optional[Cart])
async def get_cart(user_id: str):
    """Get user's cart."""
    cart = await carts_collection.find_one({"user_id": user_id})
    return cart

@app.post("/cart", response_model=Cart)
async def add_to_cart(user_id: str, item: CartItem):
    """Add item to cart."""
    # Verify shoe exists and has the requested size
    shoe = await get_shoe_by_id(str(item.shoe_id))
    if not shoe:
        raise HTTPException(status_code=404, detail="Shoe not found")
    
    # Check if size is available
    size_available = any(
        size_info["size"] == item.size and size_info["quantity"] >= item.quantity
        for size_info in shoe["sizes"]
    )
    if not size_available:
        raise HTTPException(status_code=400, detail="Size not available or insufficient quantity")
    
    # Find or create cart
    cart = await carts_collection.find_one({"user_id": user_id})
    
    if cart:
        # Update existing cart
        existing_item = None
        for i, cart_item in enumerate(cart["items"]):
            if cart_item["shoe_id"] == item.shoe_id and cart_item["size"] == item.size:
                existing_item = i
                break
        
        if existing_item is not None:
            cart["items"][existing_item]["quantity"] += item.quantity
        else:
            cart["items"].append(item.dict())
        
        cart["updated_at"] = datetime.utcnow()
        
        await carts_collection.update_one(
            {"_id": cart["_id"]},
            {"$set": {"items": cart["items"], "updated_at": cart["updated_at"]}}
        )
    else:
        # Create new cart
        cart_dict = {
            "user_id": user_id,
            "items": [item.dict()],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = await carts_collection.insert_one(cart_dict)
        cart = await carts_collection.find_one({"_id": result.inserted_id})
    
    return cart

@app.delete("/cart/{user_id}/item")
async def remove_from_cart(user_id: str, shoe_id: str, size: SizeEnum):
    """Remove item from cart."""
    if not ObjectId.is_valid(shoe_id):
        raise HTTPException(status_code=400, detail="Invalid shoe ID")
    
    cart = await carts_collection.find_one({"user_id": user_id})
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    # Remove the item
    cart["items"] = [
        item for item in cart["items"]
        if not (item["shoe_id"] == ObjectId(shoe_id) and item["size"] == size)
    ]
    cart["updated_at"] = datetime.utcnow()
    
    await carts_collection.update_one(
        {"_id": cart["_i