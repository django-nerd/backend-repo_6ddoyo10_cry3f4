import os
from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Any, Dict, Optional
from bson import ObjectId
from datetime import datetime
import re

from database import db, create_document, get_documents
from schemas import (
    User,
    Product,
    Model as ModelSchema,
    Club as ClubSchema,
    Gig as GigSchema,
    Application as ApplicationSchema,
    Message as MessageSchema,
    Contract as ContractSchema,
    Report as ReportSchema,
)

app = FastAPI(title="V.I.P. Talent Network API")

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
    return {"message": "V.I.P. Talent Network API running"}


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


# ----- Schema endpoint -----
@app.get("/schema")
def get_schema():
    return {
        "user": User.model_json_schema(),
        "product": Product.model_json_schema(),
        "model": ModelSchema.model_json_schema(),
        "club": ClubSchema.model_json_schema(),
        "gig": GigSchema.model_json_schema(),
        "application": ApplicationSchema.model_json_schema(),
        "message": MessageSchema.model_json_schema(),
        "contract": ContractSchema.model_json_schema(),
        "report": ReportSchema.model_json_schema(),
    }


# ---------- Safety helpers ----------
PII_PATTERNS = [
    re.compile(r"\\b\\+?1?[-. (]*\\d{3}[-. )]*\\d{3}[-. ]*\\d{4}\\b"),  # phone numbers
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"),  # emails
    re.compile(r"instagram\\.com|@([A-Za-z0-9_]{3,})", re.IGNORECASE),  # socials
]


def detect_pii(text: str) -> tuple[bool, Optional[str]]:
    reasons: list[str] = []
    for pat in PII_PATTERNS:
        if pat.search(text or ""):
            reasons.append(pat.pattern)
    return (len(reasons) > 0, "; ".join(reasons) if reasons else None)


# ----- Seed demo data for Ontario (Toronto, Burlington, Hamilton) -----
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

    if club_count < 6:
        demo_clubs = [
            {"name": "Goldleaf", "city": "Toronto", "contact_name": "Renee", "contact_email": "talent@goldleaf.to"},
            {"name": "Harbour & Co.", "city": "Toronto", "contact_name": "Dev", "contact_email": "events@harbourco.ca"},
            {"name": "Steel & Velvet", "city": "Hamilton", "contact_name": "Arjun", "contact_email": "vip@steelvelvet.ca"},
            {"name": "Lakeside Room", "city": "Burlington", "contact_name": "Kate", "contact_email": "bookings@lakesideroom.ca"},
            {"name": "Night Atlas", "city": "Toronto", "contact_name": "Marco", "contact_email": "host@nightatlas.ca"},
            {"name": "The Foundry", "city": "Hamilton", "contact_name": "Nora", "contact_email": "events@foundryham.ca"},
        ]
        for c in demo_clubs:
            try:
                create_document("club", ClubSchema(**c))
                created_clubs += 1
            except Exception:
                pass

    if model_count < 12:
        demo_models = [
            {"name": "Ava Collins", "city": "Toronto", "bio": "Calm VIP table energy; bilingual (EN/ES).", "experience_years": 3, "hourly_rate": 55, "skills": ["VIP","Bottle Service","Bilingual"], "photos": ["https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800"]},
            {"name": "Maya Singh", "city": "Burlington", "bio": "Friendly check-in lead with QR mastery.", "experience_years": 2, "hourly_rate": 45, "skills": ["Hostess","Front Desk"], "photos": ["https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800"]},
            {"name": "Sofia Rossi", "city": "Toronto", "bio": "Leads bottle parades; team-first.", "experience_years": 5, "hourly_rate": 70, "skills": ["Bottle Service","VIP","Team Lead"], "photos": ["https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800"]},
            {"name": "Isabella Nguyen", "city": "Hamilton", "bio": "Promo model with guest flow instincts.", "experience_years": 2, "hourly_rate": 48, "skills": ["Promo","Greeter"], "photos": ["https://images.unsplash.com/photo-1554151228-14d9def656e4?w=800"]},
            {"name": "Layla Patel", "city": "Toronto", "bio": "Detail-first host; tech-forward.", "experience_years": 6, "hourly_rate": 65, "skills": ["VIP","Check-in","Hostess"], "photos": ["https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=800"]},
            {"name": "Emily Carter", "city": "Burlington", "bio": "Ocean-calm presence with sharp instincts.", "experience_years": 4, "hourly_rate": 58, "skills": ["VIP","Hostess","Bottle Service"], "photos": ["https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800"]},
            {"name": "Nina Petrova", "city": "Toronto", "bio": "Promo + VIP hybrid; great with content.", "experience_years": 3, "hourly_rate": 52, "skills": ["Model","Promo","VIP"], "photos": ["https://images.unsplash.com/photo-1544005316-04ae1f6bdfd3?w=800"]},
            {"name": "Jasmine Ray", "city": "Hamilton", "bio": "Red-carpet guest journey specialist.", "experience_years": 5, "hourly_rate": 68, "skills": ["Hostess","VIP","Front Desk"], "photos": ["https://images.unsplash.com/photo-1527980965255-d3b416303d12?w=800"]},
            {"name": "Camila Alvarez", "city": "Toronto", "bio": "Bottle show choreography finesse.", "experience_years": 4, "hourly_rate": 62, "skills": ["Bottle Service","VIP","Promo"], "photos": ["https://images.unsplash.com/photo-1520975916090-3105956fcd7a?w=800"]},
            {"name": "Aria Kim", "city": "Toronto", "bio": "Bilingual KR/EN; thrives in rush.", "experience_years": 2, "hourly_rate": 44, "skills": ["Registration","Greeter","Bilingual"], "photos": ["https://images.unsplash.com/photo-1544006659-f0b21884ce1d?w=800"]},
            {"name": "Victoria Adams", "city": "Hamilton", "bio": "Bottle service lead; crisp service.", "experience_years": 7, "hourly_rate": 75, "skills": ["Bottle Service","VIP","Lead"], "photos": ["https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=800"]},
            {"name": "Zoe Martin", "city": "Burlington", "bio": "Promo heartbeat; smiles steady.", "experience_years": 3, "hourly_rate": 45, "skills": ["Promo","Sampling","Greeter"], "photos": ["https://images.unsplash.com/photo-1547425260-76bcadfb4f2c?w=800"]},
        ]
        for m in demo_models:
            try:
                create_document("model", ModelSchema(**m))
                created_models += 1
            except Exception:
                pass

    if gig_count < 10:
        demo_gigs = [
            {"title": "Bottle Service – Grand Opening", "club_name": "Goldleaf", "city": "Toronto", "role": "Bottle Service", "date": "Fri 10:00PM–2:00AM", "location": "King West", "pay": "$60/hr + tips + $100 peak bonus", "dress_code": "All black chic, heels", "requirements": ["Bottle service exp","Parade leadership"], "spots": 4, "notes": "Peak bonus 11:30PM–1:30AM."},
            {"title": "VIP Hostess – Members Night", "club_name": "Harbour & Co.", "city": "Toronto", "role": "Host", "date": "Sat 9:00PM–3:00AM", "location": "Harbourfront", "pay": "$58/hr + tips", "dress_code": "Elegant black", "requirements": ["Check-in","Seating"], "spots": 3, "notes": "Whole night preferred."},
            {"title": "Promo Model – Sunset Launch", "club_name": "Lakeside Room", "city": "Burlington", "role": "Event Model", "date": "Fri 6:00PM–10:00PM", "location": "Waterfront", "pay": "$45/hr + merch", "dress_code": "On-brand wardrobe", "requirements": ["Sampling","On-camera"], "spots": 5, "notes": "Golden hour content."},
            {"title": "Door Hostess – Fashion Afterparty", "club_name": "Night Atlas", "city": "Toronto", "role": "Host", "date": "Wed 9:00PM–1:00AM", "location": "Queen West", "pay": "$60/hr (flat) + ride", "dress_code": "Black + metallic", "requirements": ["Guestlist","PR coordination"], "spots": 4, "notes": "Discretion required."},
            {"title": "VIP Bottle – Tech Summit", "club_name": "Steel & Velvet", "city": "Hamilton", "role": "Bottle Service", "date": "Tue 8:30PM–1:30AM", "location": "Downtown", "pay": "$68/hr + tips + $75 closing bonus", "dress_code": "Modern black", "requirements": ["Bottle service","Corporate etiquette"], "spots": 5, "notes": "Whole night preferred."},
            {"title": "Concierge Host – Members Night", "club_name": "Goldleaf", "city": "Toronto", "role": "Host", "date": "Fri 8:00PM–1:00AM", "location": "King West", "pay": "$55/hr + loyalty bonus", "dress_code": "Minimalist black", "requirements": ["Member check-in","Escorts"], "spots": 2, "notes": "Clienteling focus."},
            {"title": "Rooftop Greeter – Sessions", "club_name": "Harbour & Co.", "city": "Toronto", "role": "Host", "date": "Thu 7:00PM–11:00PM", "location": "Rooftop", "pay": "$45/hr (flat)", "dress_code": "Smart-casual", "requirements": ["Registration tablets","Line flow"], "spots": 2, "notes": "Short 4‑hour shift."},
            {"title": "Peak Hours Bottle – DJ Residency", "club_name": "Night Atlas", "city": "Toronto", "role": "Bottle Service", "date": "Sat 11:00PM–2:30AM", "location": "Queen West", "pay": "$70/hr + tips (peak)", "dress_code": "All black accessories", "requirements": ["Tray handling","Sparklers"], "spots": 6, "notes": "Few hours only – peak."},
            {"title": "Harbour Gala Hostess", "club_name": "Lakeside Room", "city": "Burlington", "role": "Host", "date": "Sun 5:00PM–10:00PM", "location": "Waterfront", "pay": "$55/hr + dinner", "dress_code": "Coastal formal", "requirements": ["Seating charts","Warm greeting"], "spots": 3, "notes": "Ends by 10PM."},
            {"title": "Launch Promo Team", "club_name": "The Foundry", "city": "Hamilton", "role": "Brand Ambassador", "date": "Fri 6:00PM–10:00PM", "location": "Corktown", "pay": "$50/hr + content credit", "dress_code": "On-brand", "requirements": ["Sampling","Talking points"], "spots": 5, "notes": "Half‑night promo push."},
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


# ----- Models (Talent) -----
@app.post("/api/models")
def create_model(payload: ModelSchema):
    new_id = create_document("model", payload)
    return {"id": new_id}


@app.get("/api/models")
def list_models(city: Optional[str] = None, skill: Optional[str] = None):
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
def list_clubs(city: Optional[str] = None):
    query: Dict[str, Any] = {"city": city} if city else {}
    docs = get_documents("club", query)
    return [_serialize(d) for d in docs]


# ----- Gigs (Job posts) -----
@app.post("/api/gigs")
def create_gig(payload: GigSchema):
    new_id = create_document("gig", payload)
    return {"id": new_id}


@app.get("/api/gigs")
def list_gigs(city: Optional[str] = None, role: Optional[str] = None):
    query: Dict[str, Any] = {}
    if city:
        query["city"] = city
    if role:
        query["role"] = role
    docs = get_documents("gig", query)
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
def list_applications(gig_id: Optional[str] = None, model_id: Optional[str] = None):
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


# ----- Messaging (Safety Hub) -----
@app.post("/api/messages")
def send_message(payload: MessageSchema):
    pii, reason = detect_pii(payload.text)
    data = payload.model_dump()
    data["pii_flag"] = bool(pii)
    data["pii_reason"] = reason
    new_id = create_document("message", MessageSchema(**data))
    return {"id": new_id, "pii_flag": data["pii_flag"], "pii_reason": data["pii_reason"]}


@app.get("/api/messages")
def get_messages(thread_id: str = Query(...)):
    docs = get_documents("message", {"thread_id": thread_id})
    docs.sort(key=lambda d: d.get("created_at"), reverse=False)
    return [_serialize(d) for d in docs]


@app.get("/api/messages/threads")
def list_threads(limit: int = 20):
    # Aggregate distinct thread_ids with last message
    pipeline = [
        {"$sort": {"created_at": -1}},
        {"$group": {"_id": "$thread_id", "last": {"$first": "$$ROOT"}, "count": {"$sum": 1}}},
        {"$limit": int(limit)}
    ]
    try:
        results = list(db["message"].aggregate(pipeline))
    except Exception:
        results = []
    threads = []
    for r in results:
        last = _serialize(r.get("last") or {})
        threads.append({
            "thread_id": r.get("_id"),
            "last_message": last.get("text"),
            "last_at": last.get("created_at"),
            "count": r.get("count", 0),
        })
    return threads


# ----- Contracts & Compliance -----
CONTRACT_TEMPLATE = (
    "This Contract confirms the engagement between {client_name} at {venue} in {city} and Talent ID {talent_id} for the role of {role} on {date} from {start_time} to {end_time}. Base Pay: {base_pay}. Gratuity: {gratuity}. Both parties agree to professional conduct and in-app communication."
)


@app.post("/api/contracts")
def create_contract(payload: ContractSchema):
    data = payload.model_dump()
    if not data.get("contract_text"):
        data["contract_text"] = CONTRACT_TEMPLATE.format(**{
            "client_name": data.get("client_name", "Client"),
            "venue": data.get("venue", "Venue"),
            "city": data.get("city", "City"),
            "talent_id": data.get("talent_id", ""),
            "role": data.get("role", "Role"),
            "date": data.get("date", "Date"),
            "start_time": data.get("start_time", ""),
            "end_time": data.get("end_time", ""),
            "base_pay": data.get("base_pay", "TBD"),
            "gratuity": data.get("gratuity", "as per venue policy"),
        })
    new_id = create_document("contract", ContractSchema(**data))
    return {"id": new_id}


@app.get("/api/contracts")
def list_contracts(talent_id: Optional[str] = None, client_id: Optional[str] = None, status: Optional[str] = None):
    query: Dict[str, Any] = {}
    if talent_id:
        query["talent_id"] = talent_id
    if client_id:
        query["client_id"] = client_id
    if status:
        query["status"] = status
    docs = get_documents("contract", query)
    docs.sort(key=lambda d: d.get("created_at"), reverse=True)
    return [_serialize(d) for d in docs]


@app.post("/api/contracts/{contract_id}/sign")
def sign_contract(contract_id: str, actor: str = Query(..., pattern="^(talent|client)$")):
    try:
        _id = ObjectId(contract_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid contract id")
    coll = db["contract"]
    doc = coll.find_one({"_id": _id})
    if not doc:
        raise HTTPException(status_code=404, detail="Contract not found")
    now = datetime.utcnow().isoformat()
    update: Dict[str, Any] = {"status": doc.get("status", "pending")}
    if actor == "talent":
        update["signed_talent_at"] = now
        update["status"] = "active" if not doc.get("signed_client_at") else "active"
    else:
        update["signed_client_at"] = now
        update["status"] = "active" if not doc.get("signed_talent_at") else "active"
    coll.update_one({"_id": _id}, {"$set": update})
    return {"ok": True, **update}


@app.post("/api/contracts/{contract_id}/checkin")
def contract_checkin(contract_id: str, time: Optional[str] = Body(default=None)):
    try:
        _id = ObjectId(contract_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid contract id")
    now = time or datetime.utcnow().isoformat()
    db["contract"].update_one({"_id": _id}, {"$set": {"check_in": now}})
    return {"ok": True, "check_in": now}


@app.post("/api/contracts/{contract_id}/checkout")
def contract_checkout(contract_id: str, time: Optional[str] = Body(default=None)):
    try:
        _id = ObjectId(contract_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid contract id")
    now = time or datetime.utcnow().isoformat()
    db["contract"].update_one({"_id": _id}, {"$set": {"check_out": now, "status": "completed"}})
    return {"ok": True, "check_out": now, "status": "completed"}


# ----- Reports -----
@app.post("/api/reports")
def create_report(payload: ReportSchema):
    new_id = create_document("report", payload)
    return {"id": new_id}


@app.get("/api/reports")
def list_reports(limit: int = 50):
    docs = get_documents("report", {})[: int(limit)]
    return [_serialize(d) for d in docs]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
