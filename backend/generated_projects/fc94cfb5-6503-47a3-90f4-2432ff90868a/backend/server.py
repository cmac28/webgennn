# server.py
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, EmailStr, validator
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
from datetime import datetime
import os
from pathlib import Path
import uuid
import shutil

# Pydantic Models
class ContactForm(BaseModel):
    name: str
    email: EmailStr
    phone: str
    service_type: str
    message: str
    preferred_contact: Optional[str] = "email"
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @validator('phone')
    def phone_validation(cls, v):
        # Basic phone validation
        cleaned_phone = ''.join(filter(str.isdigit, v))
        if len(cleaned_phone) < 10:
            raise ValueError('Phone number must be at least 10 digits')
        return v

class QuoteRequest(BaseModel):
    contact_info: ContactForm
    project_details: str
    estimated_budget: Optional[str] = None
    timeline: Optional[str] = None
    property_type: str  # residential, commercial
    square_footage: Optional[int] = None

class ServiceCategory(BaseModel):
    id: str
    name: str
    description: str
    image_url: Optional[str] = None
    features: List[str]
    starting_price: Optional[str] = None

class ProjectGallery(BaseModel):
    id: str
    title: str
    description: str
    service_category: str
    images: List[str]
    completion_date: datetime
    client_testimonial: Optional[str] = None

class NewsletterSubscription(BaseModel):
    email: EmailStr
    name: Optional[str] = None

# Database connection
class Database:
    client: AsyncIOMotorClient = None

db = Database()

async def get_database() -> AsyncIOMotorClient:
    return db.client

async def get_collection(collection_name: str):
    client = await get_database()
    return client.renovation_business[collection_name]

# FastAPI app initialization
app = FastAPI(
    title="Renovation Business API",
    description="Modern renovation business website backend",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Startup and shutdown events
@app.on_event("startup")
async def startup_db_client():
    db.client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    
    # Initialize default services
    services_collection = await get_collection("services")
    existing_services = await services_collection.count_documents({})
    
    if existing_services == 0:
        default_services = [
            {
                "id": "flooring",
                "name": "Flooring Solutions",
                "description": "Premium flooring installation including hardwood, tile, vinyl, and specialty epoxy flooring",
                "features": ["Epoxy Flooring", "Hardwood Installation", "Tile Work", "Vinyl Plank", "Floor Refinishing"],
                "starting_price": "$5/sq ft"
            },
            {
                "id": "bathrooms",
                "name": "Bathroom Renovation",
                "description": "Complete bathroom remodeling from design to completion",
                "features": ["Custom Vanities", "Tile Installation", "Plumbing", "Lighting", "Accessibility Features"],
                "starting_price": "$8,000"
            },
            {
                "id": "kitchens",
                "name": "Kitchen Remodeling",
                "description": "Transform your kitchen with modern design and functionality",
                "features": ["Custom Cabinets", "Countertop Installation", "Appliance Integration", "Backsplash", "Island Design"],
                "starting_price": "$15,000"
            },
            {
                "id": "full-house",
                "name": "Full House Renovation",
                "description": "Complete home transformation and renovation services",
                "features": ["Structural Work", "Electrical", "Plumbing", "Flooring", "Paint & Finishes", "Project Management"],
                "starting_price": "Contact for Quote"
            }
        ]
        await services_collection.insert_many(default_services)

@app.on_event("shutdown")
async def shutdown_db_client():
    db.client.close()

# Routes

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Premium Renovations</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <h1>Premium Renovations API</h1>
        <p>Welcome to our renovation business backend API.</p>
        <p><a href="/docs">View API Documentation</a></p>
    </body>
    </html>
    """

@app.get("/api/services", response_model=List[ServiceCategory])
async def get_services():
    """Get all renovation services"""
    try:
        services_collection = await get_collection("services")
        services = await services_collection.find({}).to_list(1000)
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/services/{service_id}", response_model=ServiceCategory)
async def get_service(service_id: str):
    """Get specific service details"""
    try:
        services_collection = await get_collection("services")
        service = await services_collection.find_one({"id": service_id})
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        return service
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/contact")
async def submit_contact_form(contact_form: ContactForm):
    """Submit contact form"""
    try:
        contact_collection = await get_collection("contacts")
        contact_data = contact_form.dict()
        contact_data["submitted_at"] = datetime.utcnow()
        contact_data["status"] = "new"
        
        result = await contact_collection.insert_one(contact_data)
        
        # TODO: Send email notification to business owner
        # TODO: Send confirmation email to customer
        
        return {
            "message": "Contact form submitted successfully",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quote")
async def request_quote(quote_request: QuoteRequest):
    """Submit quote request"""
    try:
        quotes_collection = await get_collection("quotes")
        quote_data = quote_request.dict()
        quote_data["submitted_at"] = datetime.utcnow()
        quote_data["status"] = "pending"
        quote_data["quote_number"] = f"QT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        result = await quotes_collection.insert_one(quote_data)
        
        return {
            "message": "Quote request submitted successfully",
            "quote_number": quote_data["quote_number"],
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gallery", response_model=List[ProjectGallery])
async def get_project_gallery():
    """Get project gallery"""
    try:
        gallery_collection = await get_collection("gallery")
        projects = await gallery_collection.find({}).sort("completion_date", -1).to_list(1000)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gallery/{category}")
async def get_gallery_by_category(category: str):
    """Get gallery filtered by service category"""
    try:
        gallery_collection = await get_collection("gallery")
        projects = await gallery_collection.find(
            {"service_category": category}
        ).sort("completion_date", -1).to_list(1000)
        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/newsletter")
async def subscribe_newsletter(subscription: NewsletterSubscription):
    """Subscribe to newsletter"""
    try:
        newsletter_collection = await get_collection("newsletter")
        
        # Check if email already exists
        existing = await newsletter_collection.find_one({"email": subscription.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already subscribed")
        
        subscription_data = subscription.dict()
        subscription_data["subscribed_at"] = datetime.utcnow()
        subscription_data["active"] = True
        
        await newsletter_collection.insert_one(subscription_data)
        
        return {"message": "Successfully subscribed to newsletter"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload-image")
async def upload_image(file: UploadFile = File(...), category: str = Form(...)):
    """Upload project image"""
    try:
        # Validate file type
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        # Create upload directory if it doesn't exist
        upload_dir = Path("static/uploads")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        file_extension = file.filename.split(".")[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return {
            "message": "Image uploaded successfully",
            "filename": unique_filename,
            "url": f"/static/uploads/{unique_filename}"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/company-info")
async def get_company_info():
    """Get company information"""
    return {
        "name": "Premium Renovations",
        "tagline": "Transforming spaces, exceeding expectations",
        "description": "Professional renovation services with over 10 years of experience",
        "phone": "(555) 123-4567",
        "email": "info@premiumrenovations.com",
        "address": {
            "street": "123 Construction Ave",
            "city": "Your City",
            "state": "Your State",
            "zip": "12345"
        },
        "business_hours": {
            "monday": "8:00 AM - 6:00 PM",
            "tuesday": "8:00 AM - 6:00 PM",
            "wednesday": "8:00 AM - 6:00 PM",
            "thursday": "8:00 AM - 6:00 PM",
            "friday": "8:00 AM - 6:00 PM",
            "saturday": "9:00 AM - 4:00 PM",
            "sunday": "Closed"
        },
        "social_media": {
            "facebook": "https://facebook.com/premiumrenovations",
            "instagram": "https://instagram.com/premiumrenovations",
            "linkedin": "https://linkedin.com/company/premiumrenovations"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)