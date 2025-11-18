import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Any, Dict
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Model as ModelSchema, Club as ClubSchema, Gig as GigSchema, Application as ApplicationSchema

app = FastAPI(title="Hostess & Club Night Job Board API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Convert Mongo ObjectId and datetimes to strings for JSON response"""
    if not doc:
        return doc
    d = dict(doc)
    _id = d.get("_id")
    if isinstance(_id, ObjectId):
        d["id"] = str(_id)
        del d["_id"]
    # Convert nested ObjectIds or datetimes if necessary
    for k, v in list(d.items()):
        if isinstance(v, ObjectId):
            d[k] = str(v)
        elif hasattr(v, "isoformat"):
            try:
                d[k] = v.isoformat()
            except Exception:
                pass
    return d


@app.get("/")
def read_root():
    return {"message": "Hostess & Club Nights API running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# ----- Schema endpoint for viewers/tools -----
from schemas import User, Product, Model as ModelSchemaRef, Club as ClubSchemaRef, Gig as GigSchemaRef, Application as ApplicationSchemaRef

@app.get("/schema")
def get_schema():
    return {
        "user": User.model_json_schema(),
        "product": Product.model_json_schema(),
        "model": ModelSchemaRef.model_json_schema(),
        "club": ClubSchemaRef.model_json_schema(),
        "gig": GigSchemaRef.model_json_schema(),
        "application": ApplicationSchemaRef.model_json_schema(),
    }


# ----- Seed demo data (beautiful placeholder models + detailed gigs) -----
@app.post("/api/seed")
def seed_demo():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    model_count = db["model"].count_documents({})
    gig_count = db["gig"].count_documents({})
    club_count = db["club"].count_documents({})

    created_models = 0
    created_gigs = 0
    created_clubs = 0

    # Seed clubs first (used in gigs)
    if club_count < 6:
        demo_clubs = [
            {"name": "Blue Flame", "city": "Miami", "contact_name": "Luca", "contact_email": "bookings@blueflame.miami"},
            {"name": "Neon Room", "city": "Las Vegas", "contact_name": "Jess", "contact_email": "events@neonroom.vegas"},
            {"name": "Skyline", "city": "New York", "contact_name": "Adrian", "contact_email": "host@skylinenyc.com"},
            {"name": "Echo", "city": "Los Angeles", "contact_name": "Maya", "contact_email": "talent@echo.la"},
            {"name": "Aurora", "city": "Chicago", "contact_name": "Samir", "contact_email": "vip@aurorachi.com"},
            {"name": "Harbor House", "city": "San Diego", "contact_name": "Riley", "contact_email": "events@harborhouse.sd"},
        ]
        for c in demo_clubs:
            try:
                create_document("club", ClubSchema(**c))
                created_clubs += 1
            except Exception:
                pass

    # Seed beautiful placeholder models with bios and photos
    if model_count < 12:
        demo_models = [
            {
                "name": "Ava Collins",
                "city": "Miami",
                "bio": "Sunset lover, fluent in Spanish, known for calm VIP table energy and immaculate timing.",
                "experience_years": 3,
                "hourly_rate": 55,
                "skills": ["VIP", "Bottle Service", "Promo", "Bilingual"],
                "photos": [
                    "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800",
                    "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800"
                ],
                "instagram": "@ava.collins",
                "phone": "+1-305-555-0172",
            },
            {
                "name": "Mia Lopez",
                "city": "New York",
                "bio": "Broadway-bright smile, concierge-level hostess focused on smooth check-ins and VIP care.",
                "experience_years": 4,
                "hourly_rate": 60,
                "skills": ["Hostess", "Bilingual", "Front Desk", "Greeter"],
                "photos": [
                    "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800",
                    "https://images.unsplash.com/photo-1524503033411-c9566986fc8f?w=800"
                ],
                "instagram": "@mialo.nyc",
                "phone": "+1-212-555-0146",
            },
            {
                "name": "Sofia Rossi",
                "city": "Las Vegas",
                "bio": "Italian charm meets Vegas pace. Leads bottle parades, keeps teams synced during peak hours.",
                "experience_years": 5,
                "hourly_rate": 70,
                "skills": ["Bottle Service", "VIP", "Team Lead"],
                "photos": [
                    "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800",
                    "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=800"
                ],
                "instagram": "@sofiarossi.vegas",
                "phone": "+1-702-555-0112",
            },
            {
                "name": "Isabella Nguyen",
                "city": "Los Angeles",
                "bio": "Warm, camera-comfortable promo model with a knack for guest flow and product moments.",
                "experience_years": 2,
                "hourly_rate": 48,
                "skills": ["Promo", "Greeter", "Registration"],
                "photos": [
                    "https://images.unsplash.com/photo-1554151228-14d9def656e4?w=800",
                    "https://images.unsplash.com/photo-1520975682031-c93df73c5f21?w=800"
                ],
                "instagram": "@isabellanguyen.la",
                "phone": "+1-424-555-0130",
            },
            {
                "name": "Layla Patel",
                "city": "Chicago",
                "bio": "Detail-first VIP table host, excels with tech check-in systems and high-end service.",
                "experience_years": 6,
                "hourly_rate": 65,
                "skills": ["VIP", "Check-in", "Hostess"],
                "photos": [
                    "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=800",
                    "https://images.unsplash.com/photo-1524502397800-2eeaad7c3fe5?w=800"
                ],
                "instagram": "@layla.chi",
                "phone": "+1-773-555-0168",
            },
            {
                "name": "Zoe Martin",
                "city": "Austin",
                "bio": "Hospitality heartbeat—keeps lines moving, samples flowing, smiles steady.",
                "experience_years": 3,
                "hourly_rate": 45,
                "skills": ["Promo", "Sampling", "Greeter"],
                "photos": [
                    "https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?w=800"
                ],
                "instagram": "@zoe.in.atx",
                "phone": "+1-512-555-0107",
            },
            {
                "name": "Emily Carter",
                "city": "San Diego",
                "bio": "Ocean-calm presence with sharp VIP instincts; guests remember the experience.",
                "experience_years": 4,
                "hourly_rate": 58,
                "skills": ["VIP", "Hostess", "Bottle Service"],
                "photos": [
                    "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800"
                ],
                "instagram": "@emilycsd",
                "phone": "+1-619-555-0194",
            },
            {
                "name": "Aria Kim",
                "city": "Seattle",
                "bio": "Efficient front desk lead; bilingual in Korean/English; thrives in structured chaos.",
                "experience_years": 2,
                "hourly_rate": 44,
                "skills": ["Registration", "Greeter", "Bilingual"],
                "photos": [
                    "https://images.unsplash.com/photo-1544006659-f0b21884ce1d?w=800"
                ],
                "instagram": "@aria.kim",
                "phone": "+1-206-555-0159",
            },
            {
                "name": "Victoria Adams",
                "city": "Houston",
                "bio": "Bottle show captain; keeps VIP narratives glowing and service crisp all night.",
                "experience_years": 7,
                "hourly_rate": 75,
                "skills": ["Bottle Service", "VIP", "Lead"],
                "photos": [
                    "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=800"
                ],
                "instagram": "@victoria.vip",
                "phone": "+1-713-555-0123",
            },
            {
                "name": "Nina Petrova",
                "city": "Miami",
                "bio": "International promo model; elevates brand moments and guest delight in equal measure.",
                "experience_years": 3,
                "hourly_rate": 52,
                "skills": ["Model", "Promo", "VIP"],
                "photos": [
                    "https://images.unsplash.com/photo-1544005316-04ae1f6bdfd3?w=800"
                ],
                "instagram": "@nina.miami",
                "phone": "+1-305-555-0188",
            },
            {
                "name": "Jasmine Ray",
                "city": "Los Angeles",
                "bio": "Storyteller smile; specializes in red-carpet style guest journeys and premium queues.",
                "experience_years": 5,
                "hourly_rate": 68,
                "skills": ["Hostess", "VIP", "Front Desk"],
                "photos": [
                    "https://images.unsplash.com/photo-1527980965255-d3b416303d12?w=800"
                ],
                "instagram": "@jasmine.ray",
                "phone": "+1-213-555-0170",
            },
            {
                "name": "Camila Alvarez",
                "city": "Dallas",
                "bio": "Event-savvy bottle girl with choreography finesse for parades and special moments.",
                "experience_years": 4,
                "hourly_rate": 62,
                "skills": ["Bottle Service", "VIP", "Promo"],
                "photos": [
                    "https://images.unsplash.com/photo-1520975916090-3105956fcd7a?w=800"
                ],
                "instagram": "@camila.alv",
                "phone": "+1-469-555-0190",
            },
        ]
        for m in demo_models:
            try:
                create_document("model", ModelSchema(**m))
                created_models += 1
            except Exception:
                pass

    # Seed detailed gigs for bottle girls & hostesses
    if gig_count < 10:
        demo_gigs = [
            {
                "title": "Bottle Service Parade – Grand Opening",
                "club_name": "Blue Flame",
                "city": "Miami",
                "date": "Fri 10:00PM – 2:00AM",
                "location": "South Beach",
                "pay": "$60/hr + tips + $100 peak bonus",
                "dress_code": "All black chic, heels",
                "requirements": ["Bottle service experience", "Comfortable leading parades", "Photo-friendly"],
                "spots": 4,
                "notes": "Peak bonus 11:30PM–1:30AM. Few-hour coverage available or whole night."
            },
            {
                "title": "VIP Hostess – Celebrity Table Night",
                "club_name": "Neon Room",
                "city": "Las Vegas",
                "date": "Sat 9:00PM – 4:00AM",
                "location": "The Strip",
                "pay": "$70/hr + tips",
                "dress_code": "Elegant black dress, closed-toe heels",
                "requirements": ["VIP check-in", "Guest seating", "Bilingual a plus"],
                "spots": 3,
                "notes": "Whole night preferred; peak hours 11PM–2AM."
            },
            {
                "title": "Premium Check‑In & Greeter – Rooftop Sessions",
                "club_name": "Skyline",
                "city": "New York",
                "date": "Thu 7:00PM – 11:00PM",
                "location": "Midtown rooftop",
                "pay": "$45/hr (flat)",
                "dress_code": "Monochrome smart-casual",
                "requirements": ["Registration tablets", "Line flow management", "Bilingual preferred"],
                "spots": 2,
                "notes": "Short 4‑hour shift; perfect for guestlist & QR scanning specialists."
            },
            {
                "title": "Brand Promo Team – Sunset Launch",
                "club_name": "Echo",
                "city": "Los Angeles",
                "date": "Fri 6:00PM – 10:00PM",
                "location": "West Hollywood",
                "pay": "$50/hr + merch + content credit",
                "dress_code": "On‑brand wardrobe provided",
                "requirements": ["Promo sampling", "On‑camera comfort", "Soft spoken story points"],
                "spots": 5,
                "notes": "Half‑night promo push; golden hour content capture included."
            },
            {
                "title": "VIP Table Host – Champagne Service",
                "club_name": "Aurora",
                "city": "Chicago",
                "date": "Sat 10:00PM – 3:00AM",
                "location": "River North",
                "pay": "$65/hr + tips",
                "dress_code": "Black suit‑inspired dress or tailored set",
                "requirements": ["High‑end service", "Table etiquette", "Composure under pressure"],
                "spots": 2,
                "notes": "Full‑night coverage strongly preferred."
            },
            {
                "title": "Harbor Gala Hostess – Waterfront Soirée",
                "club_name": "Harbor House",
                "city": "San Diego",
                "date": "Sun 5:00PM – 10:00PM",
                "location": "Marina District",
                "pay": "$55/hr + dinner",
                "dress_code": "Coastal formal (navy/cream)",
                "requirements": ["Seating charts", "Silent auction assist", "Warm guest greeting"],
                "spots": 3,
                "notes": "Event concludes by 10PM; content team onsite for red‑carpet arrivals."
            },
            {
                "title": "Peak Hours Bottle Girl – DJ Residency",
                "club_name": "Blue Flame",
                "city": "Miami",
                "date": "Sat 11:00PM – 2:30AM",
                "location": "South Beach",
                "pay": "$70/hr + tips (peak block)",
                "dress_code": "All black with club accessories",
                "requirements": ["Tray handling", "Sparkler safety", "Team coordination"],
                "spots": 6,
                "notes": "Few hours only – peak block assignment."
            },
            {
                "title": "Concierge Host – Members Night",
                "club_name": "Neon Room",
                "city": "Las Vegas",
                "date": "Fri 8:00PM – 1:00AM",
                "location": "The Strip",
                "pay": "$58/hr + loyalty bonus",
                "dress_code": "Minimalist black, hair up",
                "requirements": ["Member check‑in", "Table escorts", "Calm problem solving"],
                "spots": 2,
                "notes": "Clienteling focus; strong memory for names is a plus."
            },
            {
                "title": "Door Hostess – Fashion Week Afterparty",
                "club_name": "Skyline",
                "city": "New York",
                "date": "Wed 9:00PM – 1:00AM",
                "location": "Chelsea",
                "pay": "$60/hr (flat) + ride home",
                "dress_code": "Black with metallic accent",
                "requirements": ["Guestlist control", "PR coordination", "Photo call timing"],
                "spots": 4,
                "notes": "High‑profile crowd; discretion required."
            },
            {
                "title": "VIP Bottle Service – Tech Summit After Dark",
                "club_name": "Echo",
                "city": "Los Angeles",
                "date": "Tue 8:30PM – 1:30AM",
                "location": "Downtown",
                "pay": "$68/hr + tips + $75 closing bonus",
                "dress_code": "Modern black, low‑profile heels",
                "requirements": ["Bottle service", "Corporate crowd etiquette", "Pace management"],
                "spots": 5,
                "notes": "Whole night preferred; must be punctual and detail‑oriented."
            },
        ]
        for g in demo_gigs:
            try:
                create_document("gig", GigSchema(**g))
                created_gigs += 1
            except Exception:
                pass

    return {
        "models_before": model_count,
        "gigs_before": gig_count,
        "clubs_before": club_count,
        "models_created": created_models,
        "gigs_created": created_gigs,
        "clubs_created": created_clubs,
        "total_models": db["model"].count_documents({}),
        "total_gigs": db["gig"].count_documents({}),
        "total_clubs": db["club"].count_documents({}),
    }


# ----- Models (Hostesses) -----
@app.post("/api/models")
def create_model(payload: ModelSchema):
    new_id = create_document("model", payload)
    return {"id": new_id}


@app.get("/api/models")
def list_models(city: str | None = None, skill: str | None = None):
    query: Dict[str, Any] = {}
    if city:
        query["city"] = city
    if skill:
        query["skills"] = {"$in": [skill]}
    docs = get_documents("model", query)
    return [_serialize(d) for d in docs]


# ----- Clubs -----
@app.post("/api/clubs")
def create_club(payload: ClubSchema):
    new_id = create_document("club", payload)
    return {"id": new_id}


@app.get("/api/clubs")
def list_clubs(city: str | None = None):
    query: Dict[str, Any] = {"city": city} if city else {}
    docs = get_documents("club", query)
    return [_serialize(d) for d in docs]


# ----- Gigs (Job posts) -----
@app.post("/api/gigs")
def create_gig(payload: GigSchema):
    new_id = create_document("gig", payload)
    return {"id": new_id}


@app.get("/api/gigs")
def list_gigs(city: str | None = None):
    query: Dict[str, Any] = {"city": city} if city else {}
    docs = get_documents("gig", query)
    # Sort newest first by created_at if available
    docs.sort(key=lambda d: d.get("created_at"), reverse=True)
    return [_serialize(d) for d in docs]


# ----- Applications -----
@app.post("/api/applications")
def apply_to_gig(payload: ApplicationSchema):
    # Basic validation: ensure referenced ids exist
    try:
        gig = db["gig"].find_one({"_id": ObjectId(payload.gig_id)})
        model = db["model"].find_one({"_id": ObjectId(payload.model_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid gig_id or model_id")

    if not gig or not model:
        raise HTTPException(status_code=404, detail="Gig or Model not found")

    new_id = create_document("application", payload)
    return {"id": new_id}


@app.get("/api/applications")
def list_applications(gig_id: str | None = None, model_id: str | None = None):
    query: Dict[str, Any] = {}
    if gig_id:
        try:
            query["gig_id"] = str(ObjectId(gig_id))
        except Exception:
            query["gig_id"] = gig_id
    if model_id:
        try:
            query["model_id"] = str(ObjectId(model_id))
        except Exception:
            query["model_id"] = model_id
    docs = get_documents("application", query)
    return [_serialize(d) for d in docs]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
