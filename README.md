# MedVerify — Doctor Verification Portal
 
A web application to verify doctors' medical registrations in real-time using NMC (National Medical Commission) records.
 
![MedVerify](https://img.shields.io/badge/MedVerify-Doctor%20Verification-2563eb?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Railway](https://img.shields.io/badge/Deployed%20on-Railway-0B0D0E?style=for-the-badge&logo=railway&logoColor=white)
 
---
 
## What It Does
 
Enter a doctor's **medical registration number** and **state medical council** — MedVerify instantly pulls their record from the NMC Indian Medical Register and tells you:
 
- ✅ Whether the doctor is **verified** or ❌ **not found**
- ⛔ Whether they are **suspended / blacklisted**
- 🎓 Their **qualifications** (MBBS, MD, MS, DNB, etc.)
- 🏥 Their **specialization**
- 🏛️ Which **state medical council** they are registered under
- 📅 Their **registration date**
- 📍 Their **address**
---
 
## Live Demo
 
🔗 [doctor-verify-production.up.railway.app](https://doctor-verify-production.up.railway.app)
 
---
 
## Data Sources
 
| Source | Purpose |
|--------|---------|
| NMC Indian Medical Register | Doctor search & verification |
| NMC Detail API | Qualifications, specialization, address |
| NMC Blacklist API | Suspended / blacklisted doctors |
 
All data is sourced directly from the **National Medical Commission (NMC)** — India's official medical regulatory body.
 
---
 
## Tech Stack
 
| Layer | Technology |
|-------|-----------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| HTTP Client | HTTPX (async) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Deployment | Railway |
 
---
 
## Local Setup
 
### Prerequisites
- Python 3.10+
- pip
### Steps
 
```bash
# 1. Clone the repo
git clone https://github.com/amankataria100/doctor-verify.git
cd doctor-verify
 
# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate
 
# 3. Install dependencies
pip install -r requirements.txt
 
# 4. Run the server
uvicorn app.main:app --reload --port 8000
```
 
Open `http://localhost:8000` in your browser.
 
---
 
## API Usage
 
### Verify a Doctor
 
```bash
POST /api/verify
```
 
**Request:**
```json
{
  "registration_number": "12-42148",
  "state_council": "Medical Council of India (MCI)",
  "year_of_admission": "2012"
}
```
 
**Response (Verified):**
```json
{
  "verified": true,
  "source": "nmc_portal",
  "doctor_name": "DEVINDER KUMAR SUHAG",
  "registration_number": "12-42148",
  "state_council": "Medical Council of India",
  "registration_date": "17/01/2012",
  "qualifications": ["M.D.'Physician'", "MD- Dermatology Venereology & Leprosy"],
  "specialization": "MD- Dermatology Venereology & Leprosy",
  "status": "Active",
  "address": "Vill.- Bohka, P.O.- Kolana Ki Dhani, Distt.- rewari, Haryana-123402",
  "blacklisted": false
}
```
 
**Response (Suspended):**
```json
{
  "verified": true,
  "status": "Suspended",
  "blacklisted": true,
  ...
}
```
 
**Response (Not Found):**
```json
{
  "verified": false,
  "error": "No exact match found for registration number 'XXXX'."
}
```
 
---
 
## Project Structure
 
```
doctor-verify/
├── app/
│   ├── main.py         # FastAPI server & routes
│   ├── verifier.py     # Verification logic & source priority
│   └── scraper.py      # NMC API integration
├── templates/
│   └── index.html      # Frontend UI
├── static/             # Static assets
├── Procfile            # Railway deployment config
├── requirements.txt
└── README.md
```
 
---
 
## How Verification Works
 
```
User Input (Reg No + State Council)
        ↓
NMC Indian Medical Register API
        ↓
Exact Match Check (Reg No + Council)
        ↓
NMC Detail API (Qualifications, Address)
        ↓
NMC Blacklist API (Suspended Check)
        ↓
Result → Verified / Suspended / Not Found
```
 
---
 
## Supported State Medical Councils
 
All 24 state medical councils are supported including:
 
- Andhra Pradesh, Assam, Bihar, Chhattisgarh, Delhi
- Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand
- Karnataka, Madhya Pradesh, Maharashtra
- Medical Council of India (MCI)
- National Medical Commission (NMC)
- Odisha, Punjab, Rajasthan, Tamil Nadu, Telangana
- Travancore Cochin (Kerala), Uttarakhand, Uttar Pradesh, West Bengal
---
 
## Limitations
 
- **Specialization** data depends on NMC's detail API — some older records may show "General Practice" if NMC has not updated their database.
- NMC portal occasionally experiences downtime. If verification fails, use the manual verification link provided in the error message.
- This tool is for **informational purposes only**. For official legal verification, always refer to [nmc.org.in](https://www.nmc.org.in).
---
 
## Disclaimer
 
This project is not affiliated with or endorsed by the National Medical Commission (NMC) or any government body. All data is publicly available on the NMC Indian Medical Register portal. Use responsibly.
 
---
 
## License
 
MIT License — free to use, modify, and distribute.
