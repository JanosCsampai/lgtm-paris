from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ServiceTypeCreate(BaseModel):
    slug: str = Field(..., examples=["tire_change"])
    name: str = Field(..., examples=["Tire Change"])
    category: str = Field(..., examples=["mechanic"])


class ServiceTypeResponse(BaseModel):
    id: str = Field(..., alias="_id")
    slug: str
    name: str
    category: str
    created_at: datetime

    model_config = {"populate_by_name": True}


def service_type_to_doc(st: ServiceTypeCreate) -> dict:
    return {
        **st.model_dump(),
        "created_at": datetime.now(timezone.utc),
    }


def doc_to_service_type(doc: dict) -> dict:
    doc["_id"] = str(doc["_id"])
    return doc
