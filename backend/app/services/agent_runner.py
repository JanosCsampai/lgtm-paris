import asyncio
from playwright.async_api import async_playwright


async def run_booking_agent(customer_data: dict, card_data: dict, appointment_data: dict):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=50)
        page = await browser.new_page()
        await page.goto("http://localhost:3000")

        # Personal details
        await page.fill("#firstname", customer_data["firstname"])
        await page.fill("#lastname", customer_data["lastname"])
        await page.fill("#email", customer_data["email"])

        # Appointment (device and time are <select> dropdowns)
        await page.select_option("#device", appointment_data["device"])
        await page.fill("#date", appointment_data["date"])  # format: YYYY-MM-DD
        await page.select_option("#time", appointment_data["time"])

        # Payment
        await page.fill("#card-number", card_data["number"])
        await page.fill("#expiry", card_data["expiry"])  # format: MM/YY
        await page.fill("#cvc", card_data["cvc"])

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
