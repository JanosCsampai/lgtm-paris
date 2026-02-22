import asyncio
import threading

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


def _run_agent_in_thread(customer_data: dict, card_data: dict, appointment_data: dict):
    """Run the async Playwright agent in a separate thread with its own event loop.
    Required on Windows: uvicorn's SelectorEventLoop doesn't support subprocesses,
    but a fresh ProactorEventLoop in a new thread does."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(run_booking_agent(customer_data, card_data, appointment_data))
    finally:
        loop.close()


@router.post("/book")
async def book(req: BookingRequest):
    card_data = {
        "number": "4242 4242 4242 4242",
        "expiry": "12/28",
        "cvc": "123",
    }
    thread = threading.Thread(
        target=_run_agent_in_thread,
        args=(
            {"firstname": req.firstname, "lastname": req.lastname, "email": req.email},
            card_data,
            {"device": req.device, "date": req.date, "time": req.time},
        ),
        daemon=True,
    )
    thread.start()
    return {"status": "success"}
