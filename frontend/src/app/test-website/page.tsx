"use client";

import { FormEvent, useRef, useState } from "react";

export default function TestWebsite() {
  const [submitted, setSubmitted] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const formRef = useRef<HTMLFormElement>(null);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const form = formRef.current!;
    const fields = [
      "firstname", "lastname", "email", "device", "date", "time",
      "card-number", "expiry", "cvc",
    ];
    const allFilled = fields.every(
      (id) => (form.querySelector(`#${id}`) as HTMLInputElement)?.value.trim() !== ""
    );

    if (!allFilled) {
      const errEl = document.getElementById("error-msg");
      errEl?.classList.remove("hidden");
      return;
    }

    const rawDate = (form.querySelector("#date") as HTMLInputElement).value;
    const time = (form.querySelector("#time") as HTMLSelectElement).value;
    const [y, m, d] = rawDate.split("-");

    setSuccessMsg(`We expect you on ${d}.${m}.${y} at ${time}.`);
    setSubmitted(true);
  }

  function handleCardNumberInput(e: React.FormEvent<HTMLInputElement>) {
    const input = e.currentTarget;
    let val = input.value.replace(/\D/g, "").slice(0, 16);
    input.value = val.replace(/(.{4})/g, "$1 ").trim();
  }

  function handleExpiryInput(e: React.FormEvent<HTMLInputElement>) {
    const input = e.currentTarget;
    let val = input.value.replace(/\D/g, "").slice(0, 4);
    if (val.length > 2) val = val.slice(0, 2) + "/" + val.slice(2);
    input.value = val;
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div id="success-box" className="w-full max-w-lg text-center">
          <div className="bg-green-500/10 border border-green-500 rounded-2xl p-12">
            <div className="text-7xl mb-6">✅</div>
            <h2 className="text-3xl font-bold text-green-400 mb-4">Booking Confirmed!</h2>
            <p id="success-msg" className="text-white text-xl leading-relaxed">{successMsg}</p>
            <p className="text-slate-400 mt-4 text-sm">A confirmation has been sent to your email address.</p>
            <button
              onClick={() => { setSubmitted(false); setSuccessMsg(""); }}
              className="mt-8 bg-slate-700 hover:bg-slate-600 text-white px-6 py-2 rounded-lg text-sm transition-colors"
            >
              New Booking
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
    <div id="form-container" className="w-full max-w-4xl">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-white">🔧 FixMyPhone</h1>
        <p className="text-slate-400 mt-2 text-lg">Fast &amp; reliable phone repair — at your doorstep.</p>
      </div>

      <div className="bg-slate-800 rounded-2xl shadow-2xl overflow-hidden grid grid-cols-1 md:grid-cols-2">
        {/* Left: Service Info */}
        <div className="bg-slate-700 p-8 flex flex-col justify-between">
          <div>
            <span className="inline-block bg-green-500 text-white text-xs font-semibold px-3 py-1 rounded-full mb-4">Popular</span>
            <h2 className="text-2xl font-bold text-white mb-3">Screen Repair</h2>
            <p className="text-slate-300 mb-6">We fix your screen in under 60 minutes. On-site or at your home — your choice.</p>
            <ul className="space-y-3 text-slate-300">
              <li className="flex items-center gap-2"><span className="text-green-400">✓</span> 12-month warranty</li>
              <li className="flex items-center gap-2"><span className="text-green-400">✓</span> Original spare parts</li>
              <li className="flex items-center gap-2"><span className="text-green-400">✓</span> Free estimate</li>
              <li className="flex items-center gap-2"><span className="text-green-400">✓</span> Certified technicians</li>
            </ul>
          </div>
          <div className="mt-8">
            <p className="text-slate-400 text-sm">Total</p>
            <p className="text-5xl font-extrabold text-white mt-1">150 <span className="text-2xl">€</span></p>
            <p className="text-slate-400 text-sm mt-1">incl. VAT</p>
          </div>
        </div>

        {/* Right: Checkout Form */}
        <div className="p-8">
          <form id="checkout-form" ref={formRef} noValidate onSubmit={handleSubmit}>
            <h3 className="text-white font-semibold text-sm uppercase tracking-widest mb-4">Personal Details</h3>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-slate-400 text-xs mb-1">First Name</label>
                <input type="text" id="firstname" required placeholder="John"
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-green-500 placeholder-slate-500" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Last Name</label>
                <input type="text" id="lastname" required placeholder="Doe"
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-green-500 placeholder-slate-500" />
              </div>
            </div>
            <div className="mb-4">
              <label className="block text-slate-400 text-xs mb-1">Email</label>
              <input type="email" id="email" required placeholder="john@example.com"
                className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-green-500 placeholder-slate-500" />
            </div>

            <h3 className="text-white font-semibold text-sm uppercase tracking-widest mb-4 mt-6">Appointment</h3>
            <div className="mb-4">
              <label className="block text-slate-400 text-xs mb-1">Device</label>
              <select id="device" required
                className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-green-500 appearance-none cursor-pointer">
                <option value="">— Please select —</option>
                <option>iPhone 14</option>
                <option>iPhone 13</option>
                <option>Samsung Galaxy S23</option>
                <option>Samsung Galaxy S22</option>
                <option>Google Pixel 7</option>
                <option>OnePlus 11</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-slate-400 text-xs mb-1">Preferred Date</label>
                <input type="date" id="date" required
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-green-500 [color-scheme:dark]" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">Time</label>
                <select id="time" required
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-green-500 appearance-none cursor-pointer">
                  <option value="">— Select —</option>
                  <option value="10:00">10:00 AM</option>
                  <option value="12:00">12:00 PM</option>
                  <option value="14:00">2:00 PM</option>
                  <option value="16:00">4:00 PM</option>
                </select>
              </div>
            </div>

            <h3 className="text-white font-semibold text-sm uppercase tracking-widest mb-4 mt-6">Payment</h3>
            <div className="mb-4">
              <label className="block text-slate-400 text-xs mb-1">Card Number</label>
              <input type="text" id="card-number" required placeholder="1234 5678 9012 3456"
                maxLength={19} inputMode="numeric" onInput={handleCardNumberInput}
                className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-green-500 placeholder-slate-500 font-mono tracking-widest" />
            </div>
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div>
                <label className="block text-slate-400 text-xs mb-1">Expiry Date</label>
                <input type="text" id="expiry" required placeholder="MM/YY" maxLength={5} onInput={handleExpiryInput}
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-green-500 placeholder-slate-500 font-mono" />
              </div>
              <div>
                <label className="block text-slate-400 text-xs mb-1">CVC</label>
                <input type="text" id="cvc" required placeholder="123" maxLength={3} inputMode="numeric"
                  className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-green-500 placeholder-slate-500 font-mono" />
              </div>
            </div>

            <p id="error-msg" className="hidden text-red-400 text-sm mb-3">Please fill in all fields.</p>

            <button type="submit"
              className="w-full bg-green-500 hover:bg-green-400 active:bg-green-600 text-white font-bold py-3 rounded-xl transition-colors duration-150 text-sm tracking-wide shadow-lg shadow-green-900/30">
              Book &amp; Pay €150 Now
            </button>

            <p className="text-slate-500 text-xs text-center mt-4">🔒 Secure payment · SSL encrypted</p>
          </form>
        </div>
      </div>
    </div>
    </div>
  );
}
