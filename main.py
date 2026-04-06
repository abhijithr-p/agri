import os
import time
import urllib.request
import urllib.parse
import json
import io
from datetime import datetime
import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient

app = FastAPI(title="Smart Farming API")

# Setup CORS to allow frontend/Vercel origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://apppozx123_db_user:i0VqQPKtCyET0Cc1@cluster0.ky23ycm.mongodb.net/")
try:
    client = MongoClient(MONGO_URI)
    db = client.smart_farming
    farmers_collection = db.farmers
except Exception as e:
    print("Database connection error:", e)

class UserRegistration(BaseModel):
    contact: str
    password: str
    crop: str
    soil: str
    land: str
    area: str
    location: str

class ListingRequest(BaseModel):
    farmer_id: str
    crop: str
    quantity: str
    price: float
    location: str
    description: str

class OfferRequest(BaseModel):
    listing_id: str
    buyer_contact: str
    offer_price: float

# --- CROP KNOWLEDGE ENGINE ---
CROP_PROFILES = {
    "Rice": {
        "irrigation": "Flood irrigation (2-5 cm standing water)",
        "water_need": "High (1500-2500 mm)",
        "stages": [
            {"name": "Land Preparation", "duration": "Weeks 1-2", "action": "Plow the field and level the soil. Ensure field is fully saturated."},
            {"name": "Transplanting", "duration": "Weeks 3-4", "action": "Plant seedlings exactly 20cm apart in standing water."},
            {"name": "Vegetative Phase (Flooding)", "duration": "Weeks 5-10", "action": "Maintain 2-5cm standing water constantly. Apply top-dressing of nitrogen."},
            {"name": "Reproductive Phase", "duration": "Weeks 11-14", "action": "Critical developmental phase. Do not let field dry out. Monitor locally for pests."},
            {"name": "Maturation & Harvest", "duration": "Weeks 15-16", "action": "Drain water entirely 10 days before harvest. Cut when 80% grains turn yellow."}
        ],
        "tips": ["Maintain standing water", "Use nitrogen fertilizer", "Monitor leaf blast disease"]
    },
    "Wheat": {
        "irrigation": "Sprinkler or Flood (critical at crown root initiation)",
        "water_need": "Medium (450-650 mm)",
        "stages": [
            {"name": "Soil Preparation", "duration": "Week 1", "action": "Prepare fine seedbed with deep plowing for optimal aeration."},
            {"name": "Sowing & Crown Root", "duration": "Weeks 2-4", "action": "Sow seeds continuously. Must apply first irrigation at 21 days (Crown Root Initiation)."},
            {"name": "Tillering & Jointing", "duration": "Weeks 5-9", "action": "Apply nitrogen fertilizers now. Avoid all water stress constraints."},
            {"name": "Heading & Flowering", "duration": "Weeks 10-14", "action": "Crucial phase for grain formation. Maintain mild soil moisture only."},
            {"name": "Harvest", "duration": "Weeks 15-18", "action": "Harvest when grains are completely hardened and moisture drops to 14%."}
        ],
        "tips": ["Avoid overwatering", "Use proper seed treatment", "Monitor for heavy rains before harvest"]
    },
    "Maize": {
        "irrigation": "Drip or Furrow irrigation",
        "water_need": "Medium (500-800 mm)",
        "stages": [
            {"name": "Land Preparation", "duration": "Weeks 1-2", "action": "Deep plow the fields and prepare dedicated ridges/furrows."},
            {"name": "Sowing & Seedling", "duration": "Weeks 3-4", "action": "Plant seeds strictly 5cm deep. Apply starter fertilizer concurrently."},
            {"name": "Vegetative Growth", "duration": "Weeks 5-8", "action": "Weed management is absolutely critical here. Apply split doses of nitrogen."},
            {"name": "Tasseling & Silking", "duration": "Weeks 9-11", "action": "Peak water demand. If it lacks moisture now, crop yields will drop massively!"},
            {"name": "Maturation & Harvest", "duration": "Weeks 12-16", "action": "Harvest when the vegetative husks dry out and kernels are visually glazed."}
        ],
        "tips": ["Weed control is essential in first 30 days", "Aerate the soil well", "Provide moisture during tasseling"]
    }
}

def get_crop_profile(crop: str):
    if not crop or not isinstance(crop, str):
        return None
        
    crop_map = {
        "rice": "Rice",
        "wheat": "Wheat",
        "maize": "Maize",
        "corn": "Maize"
    }
    normalized_crop = crop.strip().lower()
    final_key = crop_map.get(normalized_crop) or crop.strip().capitalize()
    return CROP_PROFILES.get(final_key)

# --- WEATHER AND IRRIGATION ENGINE ---
weather_cache = {}
CACHE_TTL = 300  # 5 minutes

def fetch_weather(location: str):
    global weather_cache
    
    if not location or not isinstance(location, str):
        location = "Bangalore"
        
    cache_key = location.strip().lower()
    
    # Simple Caching System
    cached_entry = weather_cache.get(cache_key)
    if cached_entry and time.time() - cached_entry["timestamp"] < CACHE_TTL:
        return cached_entry["data"]

    # Environment Variable Safety
    api_key = os.getenv("OPENWEATHER_API_KEY", "")
    fallback_data = {"temperature": 32, "humidity": 65, "condition": "Sunny", "rain": False}
    
    if not api_key:
        return fallback_data
        
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={urllib.parse.quote(location)}&appid={api_key}&units=metric"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
            # Weather Response Validation (Ensuring no missing fields)
            temp = float(data.get("main", {}).get("temp", 30))
            humidity = int(data.get("main", {}).get("humidity", 50))
            weather_list = data.get("weather", [{}])
            condition = str(weather_list[0].get("main", "Sunny") or "Sunny")
            rain = condition.lower() in ["rain", "drizzle", "thunderstorm"]
            
            result = {
                "temperature": round(temp),
                "humidity": humidity,
                "condition": condition,
                "rain": rain
            }
            
            weather_cache[cache_key] = {
                "timestamp": time.time(),
                "data": result
            }
            return result
    except Exception:
        # API Failure Handling
        return fallback_data

def get_irrigation_advice(crop: str, weather: dict):
    temp = weather.get("temperature", 30)
    humidity = weather.get("humidity", 50)
    rain = weather.get("rain", False)
    
    c = crop.strip().lower() if crop else ""
    if c == "corn": c = "maize"
    
    advice = "Maintain standard irrigation schedule."
    level = "Medium"
    
    if c == "rice":
        if rain:
            advice = "Expected rain. Reduce manual flooding."
            level = "Low"
        else:
            advice = "Always maintain standing water levels."
            level = "High"
            
    elif c == "wheat":
        if rain:
            advice = "Rainfall expected. Pause irrigation to avoid waterlogging."
            level = "Low"
        elif temp > 30:
            advice = "High temperatures. Increase watering schedule."
            level = "High"
        elif humidity > 70:
            advice = "High humidity detected. Reduce watering."
            level = "Low"
        else:
            advice = "Standard watering needed."
            level = "Medium"
            
    elif c == "maize":
        if rain:
            advice = "Sufficient natural watering. Pause drip irrigation."
            level = "Low"
        elif temp > 28:
            advice = "Dry and warm conditions. Suggest targeted watering."
            level = "Medium"
        else:
            advice = "Moderate drip irrigation required."
            level = "Medium"
            
    return {"advice": advice, "level": level}

class CropRequest(BaseModel):
    crop: str

class IrrigationRequest(BaseModel):
    crop: str
    location: str

@app.get("/weather")
async def weather_api(location: str):
    return fetch_weather(location)

@app.post("/irrigation-advice")
async def irrigation_advice(request: IrrigationRequest):
    # Security Validation
    if not request.crop or not request.location:
        raise HTTPException(status_code=400, detail="Crop and location are required.")
        
    if not get_crop_profile(request.crop):
        raise HTTPException(status_code=400, detail="Crop not supported.")
        
    try:
        weather = fetch_weather(request.location)
        advice = get_irrigation_advice(request.crop, weather)
        return {
            "weather": weather,
            "irrigation": advice
        }
    except Exception:
        return {"error": "Failed to generate irrigation advice"}

# --- ML DISEASE DETECTION ENGINE ---
DISEASE_KNOWLEDGE = {
    "leaf_blight": {
        "name": "Leaf Blight",
        "recommendation": "Apply appropriate fungicide spray immediately and ensure proper plant spacing for airflow."
    },
    "brown_spot": {
        "name": "Brown Spot",
        "recommendation": "Apply balanced soil nutrients (potassium/nitrogen) and maintain consistent moisture."
    },
    "healthy": {
        "name": "Healthy Crop",
        "recommendation": "Crop looks completely healthy. Maintain standard care and monitoring."
    }
}

import os

class DiseaseDetector:
    def __init__(self):
        # Specific Rice Leaf Disease Mapping based on Dataset Classes
        self.classes = {
            0: {"name": "Bacterial Leaf Blight", "recommendation": "Use copper-based fungicide. Avoid excessive nitrogen applications."},
            1: {"name": "Brown Spot", "recommendation": "Ensure balanced nutrition, treat seeds before planting, map proper soil drainage."},
            2: {"name": "Leaf Smut", "recommendation": "Use systemic fungicides, maintain field hygiene, destroy infected stubs post-harvest."}
        }
        self.model = None
        self.W = None
        self.b = None
        # Enforce absolute path targeting so it finds the model regardless of the CWD it's executed from
        self.model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_weights.npz")
        
    def load_model(self):
        # Load exactly once into memory bypassing unreliable Keras version mapping
        if self.model is None:
            try:
                import keras
                # Initialize the base extraction model universally
                self.model = keras.applications.MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
            except ImportError:
                import tensorflow as tf
                self.model = tf.keras.applications.MobileNetV2(weights='imagenet', include_top=False, input_shape=(224, 224, 3))

            try:
                if os.path.exists(self.model_path):
                    with np.load(self.model_path) as data:
                        self.W = data['W']
                        self.b = data['b']
                    print(f"✅ Successfully loaded optimal deterministic ML matrix from: {self.model_path}")
                else:
                    print(f"⚠️ {self.model_path} not found! Falling back to uncalculated 0-matrices.")
                    self.W = np.zeros((1280, len(self.classes)))
                    self.b = np.zeros(len(self.classes))
            except Exception as e:
                print(f"❌ Critical ML Load Error matrix: {e}")

    def _simulate(self, image: Image.Image):
        # Deprecated: Kept for historical reference. See _real_model instead.
        pass

    def _real_model(self, image: Image.Image):
        if not self.model or self.W is None:
            raise ValueError("Model failed to initialize.")
            
        # Convert image to numpy array & scale securely [0.0, 1.0] -> [-1.0, 1.0]
        img_array = np.array(image, dtype=np.float32)
        img_array = img_array / 255.0
        img_array = (img_array * 2.0) - 1.0
        
        img_array = np.expand_dims(img_array, axis=0) # Add batch dimension
        
        # 1. Extract pure structural features without triggering deserialization conflicts
        features = self.model.predict(img_array, verbose=0)
        # Average pooling equivalent mathematically
        features = np.mean(features, axis=(1, 2))
        
        # 2. Mathematical execution of Logistic Regression
        logits = np.dot(features, self.W) + self.b
        
        # 3. Secure deterministic Softmax
        exp_preds = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        predictions = exp_preds / np.sum(exp_preds, axis=1, keepdims=True)
        
        class_idx = int(np.argmax(predictions))
        confidence = float(predictions[0, class_idx])
        
        # Guard against unmapped classes safely using len() mapping
        class_idx = class_idx % len(self.classes)
        detected_info = self.classes[class_idx]
        
        return {
            "status": "success",
            "disease": detected_info["name"],
            "confidence": round(confidence, 2),
            "recommendation": detected_info["recommendation"]
        }
        
    def predict(self, image_bytes: bytes):
        try:
            # 1. IMAGE VALIDATION (Pillow verify)
            try:
                verify_img = Image.open(io.BytesIO(image_bytes))
                verify_img.verify()
            except Exception:
                return {"status": "error", "message": "Invalid image file"}

            # 2. IMAGE PROCESSING
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            image = image.resize((224, 224))
            
            # 3. MODEL INFERENCE
            return self._real_model(image)
        except Exception as e:
            print(f"Detection Error: {e}")
            return {"status": "error", "message": "Failed to analyze image"}

detector = DiseaseDetector()
# Load ML Model into RAM alongside server startup
print("Initializing Machine Learning Engine...")
detector.load_model()

@app.post("/detect-disease")
async def detect_disease(file: UploadFile = File(None)):
    if not file:
        return {"status": "error", "message": "No file uploaded"}
        
    if not file.content_type.startswith("image/"):
        return {"status": "error", "message": "Unsupported image format"}
        
    try:
        contents = await file.read()
        if not contents:
            return {"status": "error", "message": "Empty file"}
            
        if len(contents) > 10 * 1024 * 1024:
            return {"status": "error", "message": "File too large"}
            
        result = detector.predict(contents)
        return result
    except Exception:
        return {"status": "error", "message": "Internal processing error"}

# --- MARKETPLACE & AUCTION SYSTEM ---
listings_collection = db["listings"]
offers_collection = db["offers"]

@app.post("/create-listing")
async def create_listing(req: ListingRequest):
    if not req.farmer_id or not req.crop or not req.price:
        return {"status": "error", "message": "Missing required fields"}
    
    listing = {
        "farmer_id": req.farmer_id,
        "crop": req.crop,
        "quantity": req.quantity,
        "price": req.price,
        "location": req.location,
        "description": req.description,
        "created_at": datetime.utcnow().isoformat()
    }
    res = listings_collection.insert_one(listing)
    return {"status": "success", "listing_id": str(res.inserted_id)}

@app.get("/listings")
async def get_listings():
    listings_cursor = listings_collection.find().sort("created_at", -1)
    results = []
    for doc in listings_cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results

@app.post("/offer")
async def place_offer(req: OfferRequest):
    if not req.listing_id or not req.buyer_contact or not req.offer_price:
        return {"status": "error", "message": "Missing required fields"}
        
    offer = {
        "listing_id": req.listing_id,
        "buyer_contact": req.buyer_contact,
        "offer_price": req.offer_price,
        "created_at": datetime.utcnow().isoformat()
    }
    res = offers_collection.insert_one(offer)
    return {"status": "success", "offer_id": str(res.inserted_id)}

@app.get("/offers/{listing_id}")
async def get_offers(listing_id: str):
    offers_cursor = offers_collection.find({"listing_id": listing_id}).sort("offer_price", -1)
    results = []
    for doc in offers_cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
    return results

@app.post("/crop-data")
async def crop_data(request: CropRequest):
    try:
        profile = get_crop_profile(request.crop)
        if not profile:
            return {"error": "Crop not supported"}
            
        return {
            "irrigation": profile.get("irrigation", "Unknown"),
            "water_need": profile.get("water_need", "Unknown"),
            "stages": profile.get("stages", []),
            "tips": profile.get("tips", [])
        }
    except Exception:
        return {"error": "Internal server error"}

@app.post("/register")
async def register(user: UserRegistration):
    # Validation Guidelines
    if not ("@" in user.contact or user.contact.isdigit()):
        raise HTTPException(status_code=400, detail="Contact must be a valid email (e.g. user@example.com) or a phone number (digits only).")
    
    if len(user.password) < 8 or not any(c.isalpha() for c in user.password) or not any(c.isdigit() for c in user.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long, containing both letters and numbers.")

    # Validate crop (Trust Validation)
    if not get_crop_profile(user.crop):
        raise HTTPException(status_code=400, detail="Crop not supported")

    # Check if user already exists
    existing_user = farmers_collection.find_one({"contact": user.contact})
    if existing_user:
        return {"message": "User already exists"}
            
    # Store in MongoDB
    farmers_collection.insert_one(user.dict())
    return {"message": "Registered successfully"}

class LoginRequest(BaseModel):
    contact: str
    password: str

@app.post("/login")
async def login(credentials: LoginRequest):
    user = farmers_collection.find_one({"contact": credentials.contact})
    if user and user.get("password") == credentials.password:
        return {
            "message": "Login successful",
            "user": {
                "contact": user.get("contact"),
                "crop": user.get("crop"),
                "soil": user.get("soil"),
                "land": user.get("land"),
                "area": user.get("area")
            }
        }
    raise HTTPException(status_code=401, detail="Invalid credentials")

if __name__ == "__main__":
    import uvicorn
    # This allows you to run `python backend/main.py` directly from anywhere
    uvicorn.run(app, host="0.0.0.0", port=8000)
