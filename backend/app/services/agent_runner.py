import asyncio
from playwright.async_api import async_playwright


async def run_booking_agent(customer_data: dict, card_data: dict, appointment_data: dict):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        page = await browser.new_page()
        await page.goto("http://localhost:3000/test-website")
        # Wait for the form to fully hydrate (Next.js dev HMR can trigger a reload
        # a moment after the initial load — wait for #firstname to be stable first)
        await page.wait_for_selector("#firstname", state="visible", timeout=15000)
        await asyncio.sleep(1)

        # Personal details (type() simulates real keypresses, character by character)
        await page.type("#firstname", customer_data["firstname"], delay=80)
        await page.type("#lastname", customer_data["lastname"], delay=80)
        await page.type("#email", customer_data["email"], delay=80)

        # Appointment (device and time are <select> dropdowns)
        await page.select_option("#device", appointment_data["device"])
        await page.fill("#date", appointment_data["date"])  # format: YYYY-MM-DD
        await page.select_option("#time", appointment_data["time"])

        # Payment
        await page.type("#card-number", card_data["number"], delay=80)
        await page.type("#expiry", card_data["expiry"], delay=80)
        await page.type("#cvc", card_data["cvc"], delay=120)

        # Submit the form
        await page.click("button[type='submit']")

        # Wait for the green success box to appear, then pause so the jury can see it
        await page.wait_for_selector("#success-box", state="visible", timeout=5000)
        await asyncio.sleep(3)

        await browser.close()


if __name__ == "__main__":
    asyncio.run(run_booking_agent(
        customer_data={
            "firstname": "Max",
            "lastname": "Mustermann",
            "email": "max@example.com",
        },
        card_data={
            "number": "4242 4242 4242 4242",  # Stripe test card
            "expiry": "12/28",
            "cvc": "123",
        },
        appointment_data={
            "device": "iPhone 14",   # must match an <option> value in the dropdown
            "date": "2026-03-01",
            "time": "10:00",         # must match an <option> value in the dropdown
        },
    ))
