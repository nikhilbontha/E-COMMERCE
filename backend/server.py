from fastapi import FastAPI, APIRouter, HTTPException, Depends, Body
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
import bcrypt
import jwt
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

security = HTTPBearer()

# JWT Configuration
SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

# Models
class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"

class LoyaltyTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver" 
    GOLD = "gold"
    PLATINUM = "platinum"

class Category(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    image_url: Optional[str] = None

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    price: float
    brand: str
    category: str
    image_url: str
    specifications: dict = {}
    stock_quantity: int = 0
    warranty_months: int = 12
    rating: float = 0.0
    review_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    role: UserRole = UserRole.USER
    loyalty_points: int = 0
    loyalty_tier: LoyaltyTier = LoyaltyTier.BRONZE
    total_spent: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class CartItem(BaseModel):
    product_id: str
    quantity: int = 1

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    items: List[dict]
    total_amount: float
    discount_amount: float = 0.0
    loyalty_points_used: int = 0
    loyalty_points_earned: int = 0
    payment_method: str = "UPI"
    payment_status: str = "pending"
    order_status: str = "placed"
    shipping_address: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    product_id: str
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Request/Response Models
class UserCreate(BaseModel):
    email: str
    name: str
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class ProductCreate(BaseModel):
    name: str
    description: str
    price: float
    brand: str
    category: str
    image_url: str
    specifications: dict = {}
    stock_quantity: int = 0
    warranty_months: int = 12

class OrderCreate(BaseModel):
    items: List[CartItem]
    shipping_address: str
    loyalty_points_to_use: int = 0

class ReviewCreate(BaseModel):
    product_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user = await db.users.find_one({"id": user_id})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

def calculate_loyalty_tier(total_spent: float) -> LoyaltyTier:
    if total_spent >= 50000:
        return LoyaltyTier.PLATINUM
    elif total_spent >= 25000:
        return LoyaltyTier.GOLD
    elif total_spent >= 10000:
        return LoyaltyTier.SILVER
    else:
        return LoyaltyTier.BRONZE

def calculate_loyalty_points(amount: float) -> int:
    # 1 point per 100 rupees spent
    return int(amount // 100)

# Routes

@api_router.get("/")
async def root():
    return {"message": "ElectroMart API - Your Electronics Store"}

# Auth routes
@api_router.post("/auth/register")
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        phone=user_data.phone,
        loyalty_points=100  # Welcome bonus
    )
    
    user_dict = user.dict()
    user_dict["password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create JWT token
    token = create_jwt_token({"user_id": user.id, "email": user.email})
    
    return {
        "message": "User created successfully",
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "loyalty_points": user.loyalty_points,
            "loyalty_tier": user.loyalty_tier
        }
    }

@api_router.post("/auth/login")
async def login_user(login_data: UserLogin):
    user = await db.users.find_one({"email": login_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(login_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create JWT token
    token = create_jwt_token({"user_id": user["id"], "email": user["email"]})
    
    return {
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "loyalty_points": user["loyalty_points"],
            "loyalty_tier": user["loyalty_tier"]
        }
    }

# Product routes
@api_router.get("/products", response_model=List[Product])
async def get_products(category: Optional[str] = None, limit: int = 20):
    query = {"is_active": True}
    if category:
        query["category"] = category
    
    products = await db.products.find(query).limit(limit).to_list(limit)
    return [Product(**product) for product in products]

@api_router.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    product = await db.products.find_one({"id": product_id, "is_active": True})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product(**product)

@api_router.post("/products")
async def create_product(product_data: ProductCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    product = Product(**product_data.dict())
    await db.products.insert_one(product.dict())
    return {"message": "Product created successfully", "product_id": product.id}

# Category routes
@api_router.get("/categories")
async def get_categories():
    categories = await db.categories.find().to_list(100)
    return [Category(**category) for category in categories]

# Order routes
@api_router.post("/orders")
async def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user)):
    # Calculate order total
    total_amount = 0.0
    order_items = []
    
    for item in order_data.items:
        product = await db.products.find_one({"id": item.product_id, "is_active": True})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        if product["stock_quantity"] < item.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product['name']}")
        
        item_total = product["price"] * item.quantity
        total_amount += item_total
        
        order_items.append({
            "product_id": item.product_id,
            "name": product["name"],
            "price": product["price"],
            "quantity": item.quantity,
            "total": item_total
        })
    
    # Apply loyalty points discount
    discount_amount = 0.0
    loyalty_points_used = min(order_data.loyalty_points_to_use, current_user.loyalty_points)
    if loyalty_points_used > 0:
        # 1 point = 1 rupee discount
        discount_amount = loyalty_points_used
        total_amount = max(0, total_amount - discount_amount)
    
    # Calculate loyalty points earned
    loyalty_points_earned = calculate_loyalty_points(total_amount)
    
    # Create order
    order = Order(
        user_id=current_user.id,
        items=order_items,
        total_amount=total_amount,
        discount_amount=discount_amount,
        loyalty_points_used=loyalty_points_used,
        loyalty_points_earned=loyalty_points_earned,
        shipping_address=order_data.shipping_address
    )
    
    await db.orders.insert_one(order.dict())
    
    # Update user loyalty points and tier
    new_loyalty_points = current_user.loyalty_points - loyalty_points_used + loyalty_points_earned
    new_total_spent = current_user.total_spent + total_amount
    new_tier = calculate_loyalty_tier(new_total_spent)
    
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "loyalty_points": new_loyalty_points,
                "total_spent": new_total_spent,
                "loyalty_tier": new_tier
            }
        }
    )
    
    # Update product stock
    for item in order_data.items:
        await db.products.update_one(
            {"id": item.product_id},
            {"$inc": {"stock_quantity": -item.quantity}}
        )
    
    return {
        "message": "Order created successfully",
        "order_id": order.id,
        "total_amount": total_amount,
        "loyalty_points_earned": loyalty_points_earned,
        "new_loyalty_points": new_loyalty_points,
        "new_tier": new_tier
    }

@api_router.get("/orders")
async def get_user_orders(current_user: User = Depends(get_current_user)):
    orders = await db.orders.find({"user_id": current_user.id}).sort("created_at", -1).to_list(50)
    return [Order(**order) for order in orders]

# Review routes
@api_router.post("/reviews")
async def create_review(review_data: ReviewCreate, current_user: User = Depends(get_current_user)):
    # Check if product exists
    product = await db.products.find_one({"id": review_data.product_id, "is_active": True})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if user has already reviewed this product
    existing_review = await db.reviews.find_one({"product_id": review_data.product_id, "user_id": current_user.id})
    if existing_review:
        raise HTTPException(status_code=400, detail="You have already reviewed this product")
    
    # Create review
    review = Review(
        product_id=review_data.product_id,
        user_id=current_user.id,
        rating=review_data.rating,
        comment=review_data.comment
    )
    
    await db.reviews.insert_one(review.dict())
    
    # Update product rating
    reviews = await db.reviews.find({"product_id": review_data.product_id}).to_list(1000)
    avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
    
    await db.products.update_one(
        {"id": review_data.product_id},
        {
            "$set": {
                "rating": round(avg_rating, 1),
                "review_count": len(reviews)
            }
        }
    )
    
    return {"message": "Review created successfully"}

@api_router.get("/products/{product_id}/reviews")
async def get_product_reviews(product_id: str, limit: int = 20):
    reviews = await db.reviews.find({"product_id": product_id}).limit(limit).to_list(limit)
    return [Review(**review) for review in reviews]

# Loyalty program routes
@api_router.get("/loyalty/status")
async def get_loyalty_status(current_user: User = Depends(get_current_user)):
    return {
        "points": current_user.loyalty_points,
        "tier": current_user.loyalty_tier,
        "total_spent": current_user.total_spent,
        "benefits": {
            "bronze": {"discount": "5%", "free_shipping": False},
            "silver": {"discount": "10%", "free_shipping": True},
            "gold": {"discount": "15%", "free_shipping": True, "priority_support": True},
            "platinum": {"discount": "20%", "free_shipping": True, "priority_support": True, "exclusive_access": True}
        }
    }

# Recommendations
@api_router.get("/recommendations")
async def get_recommendations(current_user: User = Depends(get_current_user), limit: int = 6):
    # Simple recommendation based on user's order history
    orders = await db.orders.find({"user_id": current_user.id}).to_list(50)
    
    if not orders:
        # New user - recommend popular products
        products = await db.products.find({"is_active": True}).sort("rating", -1).limit(limit).to_list(limit)
    else:
        # Get categories from user's purchase history
        purchased_categories = set()
        for order in orders:
            for item in order["items"]:
                product = await db.products.find_one({"id": item["product_id"]})
                if product:
                    purchased_categories.add(product["category"])
        
        if purchased_categories:
            # Recommend products from same categories
            products = await db.products.find({
                "is_active": True,
                "category": {"$in": list(purchased_categories)}
            }).sort("rating", -1).limit(limit).to_list(limit)
        else:
            products = await db.products.find({"is_active": True}).sort("rating", -1).limit(limit).to_list(limit)
    
    return [Product(**product) for product in products]

# Mock payment endpoint
@api_router.post("/payment/simulate")
async def simulate_payment(order_id: str = Body(...), payment_method: str = Body(...)):
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Simulate payment processing
    success_rate = 0.95  # 95% success rate for demo
    import random
    if random.random() < success_rate:
        await db.orders.update_one(
            {"id": order_id},
            {"$set": {"payment_status": "completed", "order_status": "confirmed"}}
        )
        return {"status": "success", "message": f"Payment via {payment_method} successful"}
    else:
        return {"status": "failed", "message": "Payment failed, please try again"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    # Create sample categories
    categories_data = [
        {"name": "Smartphones", "description": "Latest smartphones and accessories", "image_url": "https://images.unsplash.com/photo-1498049794561-7780e7231661"},
        {"name": "Headphones", "description": "Premium audio devices", "image_url": "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9"},
        {"name": "Smartwatches", "description": "Wearable technology", "image_url": "https://images.unsplash.com/photo-1588508065123-287b28e013da"},
        {"name": "Chargers & Power Banks", "description": "Power accessories", "image_url": "https://images.unsplash.com/photo-1636115305669-9096bffe87fd"}
    ]
    
    for cat_data in categories_data:
        existing = await db.categories.find_one({"name": cat_data["name"]})
        if not existing:
            category = Category(**cat_data)
            await db.categories.insert_one(category.dict())
    
    # Create sample products
    products_data = [
        {
            "name": "iPhone 15 Pro Max",
            "description": "Latest iPhone with A17 Pro chip and titanium design",
            "price": 159900,
            "brand": "Apple",
            "category": "Smartphones",
            "image_url": "https://images.unsplash.com/photo-1498049794561-7780e7231661",
            "specifications": {
                "display": "6.7-inch Super Retina XDR",
                "storage": "256GB",
                "camera": "48MP Main, 12MP Ultra Wide",
                "battery": "4441 mAh"
            },
            "stock_quantity": 50,
            "warranty_months": 12
        },
        {
            "name": "Sony WH-1000XM5",
            "description": "Premium noise canceling headphones",
            "price": 29990,
            "brand": "Sony",
            "category": "Headphones",
            "image_url": "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9",
            "specifications": {
                "type": "Over-ear",
                "noise_canceling": "Yes",
                "battery_life": "30 hours",
                "connectivity": "Bluetooth 5.2, USB-C"
            },
            "stock_quantity": 30,
            "warranty_months": 24
        },
        {
            "name": "Apple Watch Series 9",
            "description": "Advanced smartwatch with health monitoring",
            "price": 41900,
            "brand": "Apple",
            "category": "Smartwatches",
            "image_url": "https://images.unsplash.com/photo-1588508065123-287b28e013da",
            "specifications": {
                "display": "45mm Always-On Retina",
                "health": "ECG, Blood Oxygen, Sleep Tracking",
                "battery": "18 hours",
                "water_resistance": "50 meters"
            },
            "stock_quantity": 25,
            "warranty_months": 12
        },
        {
            "name": "Anker PowerCore 20000mAh",
            "description": "High-capacity portable power bank",
            "price": 2999,
            "brand": "Anker",
            "category": "Chargers & Power Banks",
            "image_url": "https://images.unsplash.com/photo-1636115305669-9096bffe87fd",
            "specifications": {
                "capacity": "20000mAh",
                "ports": "2x USB-A, 1x USB-C",
                "fast_charging": "PowerIQ 3.0",
                "weight": "360g"
            },
            "stock_quantity": 100,
            "warranty_months": 18
        }
    ]
    
    for prod_data in products_data:
        existing = await db.products.find_one({"name": prod_data["name"]})
        if not existing:
            product = Product(**prod_data)
            await db.products.insert_one(product.dict())

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()