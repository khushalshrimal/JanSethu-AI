# JanSethu AI 2.0 — SIH Video Recording Checklist

---

## 📋 Pre-Recording Verification (Do Before Pressing Record)

- [ ] **Backend Running**: FastAPI server running on `http://localhost:8000`.
- [ ] **Frontend Running**: Vite dev server or static build running on `http://localhost:5173`.
- [ ] **Database Seeded**: Run `py scripts/seed.py` for fresh Baramati Hospital seed data.
- [ ] **Demo Health Check**: `GET http://localhost:8000/api/v1/health/demo-readiness` returns status `PASS` (12/12 checks).
- [ ] **Browser Mic Permissions**: Verify web speech API / microphone permission is granted on `http://localhost:5173`.
- [ ] **Screen Resolution**: Set display resolution to 1920x1080 (1080p) with 100% DPI scaling.
- [ ] **Browser Zoom**: Set browser zoom to 100% (or 110% for clear font visibility).
- [ ] **Clean Desktop & Browser**: Close unrelated tabs, developer tools console, terminal tracebacks, and system notification popups.
- [ ] **No Personal Data**: Ensure demo phone numbers (+91-9876543210) and demo credentials are used.

---

## 🎥 During Recording Guidelines

1. **Problem First**: Spend the first 20 seconds explaining rural basic phone accessibility.
2. **Phone Simulator**: Show the **Development Phone Simulator** header clearly. Do NOT call it "Live PSTN Call".
3. **Real Backend Booking**: Show the real confirmation ticket code (`JS-2026-XXXX`).
4. **Cross-Channel Proof**: Show the exact same appointment appearing in PWA (`/my-appointments`), Provider Dashboard (`/provider`), and Admin Audit Log (`/admin`).
5. **Keypad DTMF Fallback**: Demonstrate keypad button input to prove no speech is required.
6. **Emergency Flow**: Show emergency routing with 108 ambulance contacts. Emphasize that JanSethu does NOT diagnose.
7. **No Overclaiming**: Use statements like *"Architecture ready for cloud telephony providers (Exotel/Twilio)"* rather than claiming a live PSTN virtual number is currently connected.

---

## 🏁 Post-Recording Verification

- [ ] Video audio is clear with zero background noise.
- [ ] Screen resolution is sharp with readable text.
- [ ] Demonstration duration is strictly between 2:00 and 3:00 minutes.
