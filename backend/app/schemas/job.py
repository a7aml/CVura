import datetime as dt
import uuid

from pydantic import BaseModel

_OUT_CONFIG = {"from_attributes": True}


class JobCreate(BaseModel):
    source: str
    title: str
    company: str | None = None
    posting_url: str | None = None
    raw_description: str


class JobOut(JobCreate):
    id: uuid.UUID
    user_id: uuid.UUID
    parsed_json: dict | None = None
    created_at: dt.datetime
    model_config = _OUT_CONFIG
