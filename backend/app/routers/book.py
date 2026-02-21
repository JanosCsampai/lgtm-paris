import asyncio

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.agent_runner import run_booking_agent

router = APIRouter(prefix="/api")


class BookingRequest(BaseModel):
    firstname: str
    lastname: str
    email: str
    device: str  # must match exact <option> value in index.html
    date: str    # YYYY-MM-DD
    time: str    # HH:MM (e.g. "10:00", "12:00", "14:00", "16:00")


@router.post("/book")
async def book(req: BookingRequest):
    card_data = {
        "number": "4242 4242 4242 4242",
        "expiry": "12/28",
        "cvc": "123",
    }
    asyncio.create_task(
        run_booking_agent(
            customer_data={
                "firstname": req.firstname,
                "lastname": req.lastname,
                "email": req.email,
            },
            card_data=card_data,
            appointment_data={
                "device": req.device,
                "date": req.date,
                "time": req.time,
            },
        )
    )
    return {"status": "success"}
