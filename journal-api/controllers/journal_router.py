import logging
from typing import AsyncGenerator, Optional, List
from fastapi import APIRouter, HTTPException, Request, Depends 
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..repositories.postgres_repository import PostgresDB
from ..services import EntryService
from ..models.entry import Entry, EntryCreate, EntryUpdate
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from jose import jwt, JWTError
from datetime import datetime, timedelta
import os

# TODO: Add authentication middleware
load_dotenv()  # .env dosyasını oku

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

def create_access_token(data: dict) -> str:
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

class JWTBearer(HTTPBearer):
    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        try:
            payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
            request.state.user = payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=403, detail="Invalid or expired token")
        return credentials.credentials

# TODO: Add request validation middleware
class EntryModel(BaseModel):
    work: str = Field(..., min_length=1)
    struggle: str
    intention: Optional[str] = None
# TODO: Add rate limiting middleware
rate_limit_cache = {}

def rate_limiter(request: Request):
    ip = request.client.host
    now = datetime.utcnow()

    if ip in rate_limit_cache:
        last_seen = rate_limit_cache[ip]
        if (now - last_seen).seconds < 2:  # 1 istek/2 saniye
            raise HTTPException(status_code=429, detail="Too many requests")
    rate_limit_cache[ip] = now

# TODO: Add API versioning
router = APIRouter(prefix="/v1")

# TODO: Add response caching
response_cache = {}

async def get_entry_service() -> AsyncGenerator[EntryService, None]:

    async with PostgresDB() as db:
        yield EntryService(db)

@router.post("/login")
def login():
    # Normalde burada username/password kontrol edilir
    user_data = {"sub": "test_user"}

    access_token = create_access_token(user_data)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/entries/", dependencies=[Depends(JWTBearer())])
async def create_entry(entry: EntryCreate, entry_service: EntryService = Depends(get_entry_service)):

    entry_data = entry.model_dump()

    try:
        enriched_entry = await entry_service.create_entry(entry_data)
        await entry_service.db.create_entry(enriched_entry)

    except HTTPException as e:
        if e.status_code == 409:
            raise HTTPException(
                status_code=409,
                detail="You already have an entry for today."
            )
        raise e

    return JSONResponse(content={"detail": "Entry created successfully"}, status_code=201)

# TODO: Implement GET /entries endpoint to list all journal entries
# Example response: [{"id": "123", "work": "...", "struggle": "...", "intention": "..."}]
@router.get("/entries",response_model=List[Entry], dependencies=[Depends(JWTBearer())])
async def get_all_entries(request: Request, entry_service: EntryService = Depends(get_entry_service)):
    # TODO: Implement get all entries endpoint
    # Hint: Use PostgresDB and EntryService like other endpoints
    rate_limiter(request)

    cache_key = "all_entries"
    if cache_key in response_cache:
        return response_cache[cache_key]

    entries = await entry_service.get_all_entries()

    encoded_entries = jsonable_encoder(entries)
    response_cache[cache_key] = encoded_entries

    return encoded_entries

@router.get("/entries/{entry_id}", dependencies=[Depends(JWTBearer())])
async def get_entry(request: Request, entry_id: str, entry_service: EntryService = Depends(get_entry_service)):
    # TODO: Implement get single entry endpoint
    # Hint: Return 404 if entry not found
    rate_limiter(request)

    result = await entry_service.get_entry(entry_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entry not found")
    return result

@router.patch("/entries/{entry_id}", response_model=Entry, dependencies=[Depends(JWTBearer())])
async def update_entry(entry_id: str, entry_update: EntryUpdate, entry_service: EntryService = Depends(get_entry_service)):
    updated_data = entry_update.model_dump(exclude_none=True)

    result = await entry_service.update_entry(entry_id, updated_data)

    if not result:
        raise HTTPException(status_code=404, detail="Entry not found")

    return jsonable_encoder(result) 

# TODO: Implement DELETE /entries/{entry_id} endpoint to remove a specific entry
# Return 404 if entry not found
@router.delete("/entries/{entry_id}", dependencies=[Depends(JWTBearer())])
async def delete_entry(request: Request, entry_id: str, entry_service: EntryService = Depends(get_entry_service)):
    # TODO: Implement delete entry endpoint
    # Hint: Return 404 if entry not found
    rate_limiter(request)

    result = await entry_service.delete_entry(entry_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"detail": "Entry deleted"}

@router.delete("/entries", dependencies=[Depends(JWTBearer())])
async def delete_all_entries(request: Request):
   
    async with PostgresDB() as db:
        entry_service = EntryService(db)
        await entry_service.delete_all_entries()

    return {"detail": "All entries deleted"}