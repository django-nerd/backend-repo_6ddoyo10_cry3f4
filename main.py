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


# ----- Seed demo data (10 models, 5 gigs) -----
@app.post("/api/seed")
def seed_demo():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    model_count = db["model"].count_documents({})
    gig_count = db["gig"].count_documents({})

    created_models = 0
    created_gigs = 0

    if model_count < 10:
        demo_models = [
            {"name": "Ava Collins", "city": "Miami", "skills": ["VIP", "Bottle Service", "Promo"], "experience_years": 3, "hourly_rate": 45},
            {"name": "Mia Lopez", "city": "New York", "skills": ["Hostess", "Bilingual"], "experience_years": 2, "hourly_rate": 40},
            {"name": "Sofia Rossi", "city": "Las Vegas", "skills": ["VIP", "Front Desk"], "experience_years": 4, "hourly_rate": 55},
            {"name": "Isabella Nguyen", "city": "Los Angeles", "skills": ["Registration", "Promo", "Greeter"], "experience_years": 1, "hourly_rate": 35},
            {"name": "Layla Patel", "city": "Chicago", "skills": ["Model", "VIP", "Check-in"], "experience_years": 5, "hourly_rate": 50},
            {"name": "Zoe Martin", "city": "Austin", "skills": ["Promo", "Sampling"], "experience_years": 2, "hourly_rate": 38},
            {"name": "Emily Carter", "city": "San Diego", "skills": ["VIP", "Hostess"], "experience_years": 3, "hourly_rate": 42},
            {"name": "Aria Kim", "city": "Seattle", "skills": ["Registration", "Greeter"], "experience_years": 1, "hourly_rate": 32},
            {"name": "Victoria Adams", "city": "Houston", "skills": ["Bottle Service", "VIP"], "experience_years": 6, "hourly_rate": 60},
            {"name": "Nina Petrova", "city": "Miami", "skills": ["Model", "Promo"], "experience_years": 3, "hourly_rate": 45}
        ]
        for m in demo_models:
            try:
                create_document("model", ModelSchema(**m))
                created_models += 1
            except Exception:
                pass

    if gig_count < 5:
        demo_gigs = [
            {"title": "VIP Hostess - Grand Opening", "club_name": "Blue Flame", "city": "Miami", "date": "Fri 10PM-2AM", "pay": "$45/hr + tips", "requirements": ["VIP experience", "All black attire"], "spots": 3, "notes": "4-hour shift for opening night."},
            {"title": "Bottle Service Model", "club_name": "Neon Room", "city": "Las Vegas", "date": "Sat 9PM-4AM", "pay": "$55/hr + bonus", "requirements": ["Bottle service", "Friendly, energetic"], "spots": 4, "notes": "All-night set, peak hours 11PM-2AM."},
            {"title": "Check-in & Greeter", "club_name": "Skyline", "city": "New York", "date": "Thu 7PM-11PM", "pay": "$35/hr", "requirements": ["Registration", "Bilingual preferred"], "spots": 2, "notes": "Short 4-hour evening event."},
            {"title": "Promo Team - Launch Party", "club_name": "Echo", "city": "Los Angeles", "date": "Fri 8PM-12AM", "pay": "$40/hr + merch", "requirements": ["Promo", "Comfortable on camera"], "spots": 5, "notes": "Half-night promo push."},
            {"title": "VIP Table Host", "club_name": "Aurora", "city": "Chicago", "date": "Sat 10PM-3AM", "pay": "$50/hr + tips", "requirements": ["VIP", "High-end service"], "spots": 2, "notes": "Full-night coverage for VIP tables."}
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
        "models_created": created_models,
        "gigs_created": created_gigs,
        "total_models": db["model"].count_documents({}),
        "total_gigs": db["gig"].count_documents({})
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
