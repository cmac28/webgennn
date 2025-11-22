# server.py
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime, timedelta
from bson import ObjectId
import os
from passlib.context import CryptContext
import jwt
import uuid

# Pydantic Models
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

class MongoBaseModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Service Models
class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    price_range: str = Field(..., min_length=1, max_length=50)
    image_url: Optional[str] = None
    featured: bool = False

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    price_range: Optional[str] = Field(None, min_length=1, max_length=50)
    image_url: Optional[str] = None
    featured: Optional[bool] = None

class Service(MongoBaseModel, ServiceBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Project Models
class ProjectBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10, max_length=1000)
    service_type: str = Field(..., min_length=1, max_length=50)
    client_name: Optional[str] = Field(None, max_length=100)
    completion_date: datetime
    image_urls: List[str] = []
    featured: bool = False
    location: Optional[str] = Field(None, max_length=100)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    service_type: Optional[str] = Field(None, min_length=1, max_length=50)
    client_name: Optional[str] = Field(None, max_length=100)
    completion_date: Optional[datetime] = None
    image_urls: Optional[List[str]] = None
    featured: Optional[bool] = None
    location: Optional[str] = Field(None, max_length=100)

class Project(MongoBaseModel, ProjectBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Quote Request Models
class QuoteRequestBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=20)
    service_type: str = Field(..., min_length=1, max_length=100)
    project_description: str = Field(..., min_length=10, max_length=2000)
    square_footage: Optional[int] = Field(None, gt=0)
    preferred_timeline: Optional[str] = Field(None, max_length=100)
    budget_range: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=200)

class QuoteRequestCreate(QuoteRequestBase):
    pass

class QuoteRequestUpdate(BaseModel):
    status: Optional[str] = Field(None, regex="^(pending|in_progress|completed|cancelled)$")
    admin_notes: Optional[str] = Field(None, max_length=1000)

class QuoteRequest(MongoBaseModel, QuoteRequestBase):
    status: str = Field(default="pending", regex="^(pending|in_progress|completed|cancelled)$")
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Testimonial Models
class TestimonialBase(BaseModel):
    client_name: str = Field(..., min_length=1, max_length=100)
    rating: int = Field(..., ge=1, le=5)
    review: str = Field(..., min_length=10, max_length=1000)
    project_type: Optional[str] = Field(None, max_length=100)
    featured: bool = False

class TestimonialCreate(TestimonialBase):
    pass

class TestimonialUpdate(BaseModel):
    client_name: Optional[str] = Field(None, min_length=1, max_length=100)
    rating: Optional[int] = Field(None, ge=1, le=5)
    review: Optional[str] = Field(None, min_length=10, max_length=1000)
    project_type: Optional[str] = Field(None, max_length=100)
    featured: Optional[bool] = None

class Testimonial(MongoBaseModel, TestimonialBase):
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Admin Models
class AdminBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class AdminCreate(AdminBase):
    password: str = Field(..., min_length=8, max_length=100)

class AdminLogin(BaseModel):
    username: str
    password: str

class Admin(MongoBaseModel, AdminBase):
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Token(BaseModel):
    access_token: str
    token_type: str

# Company Info Model
class CompanyInfoBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=100)
    tagline: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., min_length=10, max_length=20)
    email: EmailStr
    address: str = Field(..., min_length=5, max_length=200)
    business_hours: dict = Field(default_factory=dict)
    social_media: dict = Field(default_factory=dict)
    about_description: str = Field(..., min_length=50, max_length=2000)
    years_experience: int = Field(..., gt=0)
    logo_url: Optional[str] = None

class CompanyInfoUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=100)
    tagline: Optional[str] = Field(None, min_length=1, max_length=200)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = Field(None, min_length=5, max_length=200)
    business_hours: Optional[dict] = None
    social_media: Optional[dict] = None
    about_description: Optional[str] = Field(None, min_length=50, max_length=2000)
    years_experience: Optional[int] = Field(None, gt=0)
    logo_url: Optional[str] = None

class CompanyInfo(MongoBaseModel, CompanyInfoBase):
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# FastAPI App Configuration
app = FastAPI(
    title="Professional Flooring Business API",
    description="Backend API for a professional flooring business website",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "flooring_business")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Database
client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

# Collections
services_collection = database.get_collection("services")
projects_collection = database.get_collection("projects")
quote_requests_collection = database.get_collection("quote_requests")
testimonials_collection = database.get_collection("testimonials")
admins_collection = database.get_collection("admins")
company_info_collection = database.get_collection("company_info")

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    admin = await admins_collection.find_one({"username": username})
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    return admin

# Routes

# Health Check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Authentication Routes
@app.post("/api/auth/login", response_model=Token)
async def login(admin_login: AdminLogin):
    admin = await admins_collection.find_one({"username": admin_login.username})
    if not admin or not verify_password(admin_login.password, admin["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token = create_access_token(data={"sub": admin["username"]})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/api/auth/register", response_model=dict)
async def register_admin(admin_create: AdminCreate, current_admin: dict = Depends(get_current_admin)):
    existing_admin = await admins_collection.find_one({"username": admin_create.username})
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(admin_create.password)
    admin_dict = admin_create.dict()
    del admin_dict["password"]
    admin_dict["hashed_password"] = hashed_password
    admin_dict["created_at"] = datetime.utcnow()
    
    result = await admins_collection.insert_one(admin_dict)
    return {"message": "Admin created successfully", "id": str(result.inserted_id)}

# Services Routes
@app.get("/api/services", response_model=List[Service])
async def get_services():
    services = []
    async for service in services_collection.find():
        services.append(Service(**service))
    return services

@app.get("/api/services/featured", response_model=List[Service])
async def get_featured_services():
    services = []
    async for service in services_collection.find({"featured": True}):
        services.append(Service(**service))
    return services

@app.get("/api/services/{service_id}", response_model=Service)
async def get_service(service_id: str):
    service = await services_collection.find_one({"_id": ObjectId(service_id)})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return Service(**service)

@app.post("/api/services", response_model=Service)
async def create_service(service: ServiceCreate, current_admin: dict = Depends(get_current_admin)):
    service_dict = service.dict()
    service_dict["created_at"] = datetime.utcnow()
    service_dict["updated_at"] = datetime.utcnow()
    
    result = await services_collection.insert_one(service_dict)
    created_service = await services_collection.find_one({"_id": result.inserted_id})
    return Service(**created_service)

@app.put("/api/services/{service_id}", response_model=Service)
async def update_service(service_id: str, service_update: ServiceUpdate, current_admin: dict = Depends(get_current_admin)):
    update_data = {k: v for k, v in service_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    result = await services_collection.update_one(
        {"_id": ObjectId(service_id)},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Service not found")
    
    updated_service = await services_collection.find_one({"_id": ObjectId(service_id)})
    return Service(**updated_service)

@app.delete("/api/services/{service_id}")
async def delete_service(service_id: str, current_admin: dict = Depends(get_current_admin)):
    result = await services_collection.delete_one({"_id": ObjectId(service_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404