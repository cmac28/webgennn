# server.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
import os
from contextlib import asynccontextmanager

# Pydantic Models
class ContactForm(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=1000)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class ContactResponse(BaseModel):
    id: str
    name: str
    email: str
    subject: str
    message: str
    created_at: datetime
    status: str = "pending"

class NewsletterSubscription(BaseModel):
    email: EmailStr
    subscribed_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class NewsletterResponse(BaseModel):
    email: str
    subscribed_at: datetime
    status: str = "active"

class LandingPageContent(BaseModel):
    hero_title: str
    hero_subtitle: str
    hero_cta_text: str
    hero_cta_link: str
    about_title: str
    about_content: str
    features: List[dict]
    testimonials: List[dict]

# Database configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "landing_page_db")

# Global variables for database
mongodb_client: AsyncIOMotorClient = None
database = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global mongodb_client, database
    mongodb_client = AsyncIOMotorClient(MONGODB_URL)
    database = mongodb_client[DATABASE_NAME]
    
    # Test connection
    try:
        await mongodb_client.admin.command('ping')
        print("Successfully connected to MongoDB!")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
    
    yield
    
    # Shutdown
    if mongodb_client:
        mongodb_client.close()

# FastAPI app initialization
app = FastAPI(
    title="Landing Page API",
    description="Backend API for a simple landing page with contact forms and newsletter subscriptions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database dependency
async def get_database():
    return database

# Routes
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the landing page HTML"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome - Landing Page</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            header { background: #2c3e50; color: white; padding: 1rem 0; position: fixed; width: 100%; top: 0; z-index: 1000; }
            nav { display: flex; justify-content: space-between; align-items: center; max-width: 1200px; margin: 0 auto; padding: 0 2rem; }
            .logo { font-size: 1.5rem; font-weight: bold; }
            nav ul { display: flex; list-style: none; }
            nav ul li { margin-left: 2rem; }
            nav ul li a { color: white; text-decoration: none; }
            .hero { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; text-align: center; padding: 150px 2rem 100px; margin-top: 60px; }
            .hero h1 { font-size: 3rem; margin-bottom: 1rem; }
            .hero p { font-size: 1.2rem; margin-bottom: 2rem; }
            .cta-button { display: inline-block; background: #e74c3c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; }
            .content { max-width: 1200px; margin: 0 auto; padding: 4rem 2rem; }
            .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin: 4rem 0; }
            .feature { background: #f8f9fa; padding: 2rem; border-radius: 8px; text-align: center; }
            footer { background: #2c3e50; color: white; text-align: center; padding: 2rem; }
            .contact-form { background: #f8f9fa; padding: 2rem; border-radius: 8px; margin: 2rem 0; }
            .form-group { margin-bottom: 1rem; }
            .form-group label { display: block; margin-bottom: 0.5rem; }
            .form-group input, .form-group textarea { width: 100%; padding: 0.75rem; border: 1px solid #ddd; border-radius: 4px; }
            .submit-btn { background: #3498db; color: white; padding: 0.75rem 2rem; border: none; border-radius: 4px; cursor: pointer; }
        </style>
    </head>
    <body>
        <header>
            <nav>
                <div class="logo">LandingPage</div>
                <ul>
                    <li><a href="#home">Home</a></li>
                    <li><a href="#about">About</a></li>
                    <li><a href="#features">Features</a></li>
                    <li><a href="#contact">Contact</a></li>
                </ul>
            </nav>
        </header>

        <section class="hero" id="home">
            <h1>Welcome to Our Amazing Product</h1>
            <p>Transform your business with our innovative solutions</p>
            <a href="#contact" class="cta-button">Get Started</a>
        </section>

        <div class="content">
            <section id="about">
                <h2>About Us</h2>
                <p>We are dedicated to providing exceptional solutions that help businesses grow and succeed in today's competitive market.</p>
            </section>

            <section id="features" class="features">
                <div class="feature">
                    <h3>Fast & Reliable</h3>
                    <p>Our platform delivers lightning-fast performance with 99.9% uptime guarantee.</p>
                </div>
                <div class="feature">
                    <h3>Easy to Use</h3>
                    <p>Intuitive design and user-friendly interface make it easy for anyone to get started.</p>
                </div>
                <div class="feature">
                    <h3>24/7 Support</h3>
                    <p>Our dedicated support team is available around the clock to help you succeed.</p>
                </div>
            </section>

            <section id="contact" class="contact-form">
                <h2>Contact Us</h2>
                <form id="contactForm">
                    <div class="form-group">
                        <label for="name">Name:</label>
                        <input type="text" id="name" name="name" required>
                    </div>
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="subject">Subject:</label>
                        <input type="text" id="subject" name="subject" required>
                    </div>
                    <div class="form-group">
                        <label for="message">Message:</label>
                        <textarea id="message" name="message" rows="5" required></textarea>
                    </div>
                    <button type="submit" class="submit-btn">Send Message</button>
                </form>
            </section>
        </div>

        <footer>
            <p>&copy; 2024 LandingPage. All rights reserved.</p>
        </footer>

        <script>
            document.getElementById('contactForm').addEventListener('submit', async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const data = Object.fromEntries(formData);
                
                try {
                    const response = await fetch('/api/contact', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(data)
                    });
                    
                    if (response.ok) {
                        alert('Message sent successfully!');
                        e.target.reset();
                    } else {
                        alert('Error sending message. Please try again.');
                    }
                } catch (error) {
                    alert('Error sending message. Please try again.');
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.post("/api/contact", response_model=dict)
async def submit_contact_form(
    contact_data: ContactForm,
    db = Depends(get_database)
):
    """Submit a contact form"""
    try:
        # Insert into database
        contact_dict = contact_data.dict()
        result = await db.contacts.insert_one(contact_dict)
        
        return {
            "success": True,
            "message": "Contact form submitted successfully",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error submitting contact form: {str(e)}")

@app.get("/api/contacts", response_model=List[dict])
async def get_contacts(
    skip: int = 0,
    limit: int = 10,
    db = Depends(get_database)
):
    """Get all contact form submissions (admin endpoint)"""
    try:
        cursor = db.contacts.find().skip(skip).limit(limit).sort("created_at", -1)
        contacts = []
        async for contact in cursor:
            contact["id"] = str(contact["_id"])
            del contact["_id"]
            contacts.append(contact)
        
        return contacts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching contacts: {str(e)}")

@app.post("/api/newsletter", response_model=dict)
async def subscribe_newsletter(
    subscription_data: NewsletterSubscription,
    db = Depends(get_database)
):
    """Subscribe to newsletter"""
    try:
        # Check if email already exists
        existing = await db.newsletter.find_one({"email": subscription_data.email})
        if existing:
            return {
                "success": True,
                "message": "Email already subscribed",
                "status": "existing"
            }
        
        # Insert new subscription
        subscription_dict = subscription_data.dict()
        result = await db.newsletter.insert_one(subscription_dict)
        
        return {
            "success": True,
            "message": "Successfully subscribed to newsletter",
            "id": str(result.inserted_id)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subscribing to newsletter: {str(e)}")

@app.get("/api/newsletter/subscribers", response_model=List[dict])
async def get_newsletter_subscribers(
    skip: int = 0,
    limit: int = 10,
    db = Depends(get_database)
):
    """Get newsletter subscribers (admin endpoint)"""
    try:
        cursor = db.newsletter.find().skip(skip).limit(limit).sort("subscribed_at", -1)
        subscribers = []
        async for subscriber in cursor:
            subscriber["id"] = str(subscriber["_id"])
            del subscriber["_id"]
            subscribers.append(subscriber)
        
        return subscribers
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subscribers: {str(e)}")

@app.get("/api/landing-content", response_model=LandingPageContent)
async def get_landing_content(db = Depends(get_database)):
    """Get landing page content"""
    try:
        content = await db.content.find_one({"page": "landing"})
        
        if not content:
            # Return default content
            default_content = {
                "hero_title": "Welcome to Our Amazing Product",
                "hero_subtitle": "Transform your business with our innovative solutions",
                "hero_cta_text": "Get Started",
                "hero_cta_link": "#contact",
                "about_title": "About Us",
                "about_content": "We are dedicated to providing exceptional solutions that help businesses grow and succeed in today's competitive market.",
                "features": [
                    {
                        "title": "Fast & Reliable",
                        "description": "Our platform delivers lightning-fast performance with 99.9% uptime guarantee.",
                        "icon": "⚡"
                    },
                    {
                        "title": "Easy to Use",
                        "description": "Intuitive design and user-friendly interface make it easy for anyone to get started.",
                        "icon": "🎯"
                    },
                    {
                        "title": "24/7 Support",
                        "description": "Our dedicated support team is available around the clock to help you succeed.",
                        "icon": "🛠️"
                    }
                ],
                "testimonials": [
                    {
                        "name": "John Doe",
                        "company": "Tech Corp",
                        "text": "This product has transformed our business operations completely!",
                        "rating": 5
                    }
                ]
            }
            return LandingPageContent(**default_content)
        
        # Remove MongoDB _id field
        del content["_id"]
        del content["page"]
        return LandingPageContent(**content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching landing content: {str(e)}")

@app.put("/api/landing-content", response_model=dict)
async def update_landing_content(
    content_data: LandingPageContent,
    db = Depends(get_database)
):
    """Update landing page content (admin endpoint)"""
    try:
        content_dict = content_data.dict()
        content_dict["page"] = "landing"
        content_dict["updated_at"] = datetime.utcnow()
        
        result = await db.content.replace_one(
            {"page": "landing"},
            content_dict,
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Landing page content updated successfully",
            "modified_count": result.modified_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating landing content: {str(e)}")

@app