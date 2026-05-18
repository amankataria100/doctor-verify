# Doctor Verification Portal

Medical registration number se doctor ko verify karo — NMC records se.

## Data Sources (priority order)
1. **Surepass NMC API** — most reliable, paid (free trial available)
2. **IDfy via RapidAPI** — freemium
3. **NMC Portal Scraper** — always available, no key needed (fallback)

## What you get
- ✅ Doctor name
- ✅ Registration number
- ✅ State Medical Council
- ✅ Registration date
- ✅ Qualifications (MBBS, MD, MS, etc.)
- ✅ Specialization (highest degree)
- ✅ Verified / Not verified status

## Setup (5 minutes)

```bash
# 1. Clone and enter
cd doctor-verify

# 2. Create virtual env
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up API keys (optional — scraper works without keys)
cp .env.example .env
# Edit .env and add your Surepass or RapidAPI key

# 5. Run
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 in browser.

## API Usage (for programmatic use)

```bash
curl -X POST http://localhost:8000/api/verify \
  -H "Content-Type: application/json" \
  -d '{
    "registration_number": "DELHI-12345",
    "state_council": "Delhi Medical Council",
    "year_of_admission": "2015"
  }'
```

### Response (verified)
```json
{
  "verified": true,
  "source": "nmc_portal",
  "doctor_name": "Dr. Ramesh Kumar",
  "registration_number": "DELHI-12345",
  "state_council": "Delhi Medical Council",
  "registration_date": "2015-03-15",
  "qualifications": ["MBBS", "MD (General Medicine)"],
  "specialization": "MD (General Medicine)",
  "status": "Active"
}
```

### Response (not found)
```json
{
  "verified": false,
  "source": "nmc_portal",
  "error": "Doctor not found. Please check registration number and state council."
}
```

## Deploy on Railway (free)

```bash
# Install Railway CLI
npm install -g @railway/cli

railway login
railway init
railway up
```

Set environment variables in Railway dashboard under Variables tab.

## Get API Keys

- **Surepass**: https://surepass.io/nmc-verification-api/ → Request Demo
- **IDfy/RapidAPI**: https://rapidapi.com/idfy-idfy-default/api/mci-nmc-doctor-verification → Subscribe (Freemium)

## Notes
- NMC portal scraper works without any API key — good for testing
- For production with high traffic → get Surepass or IDfy key
- Specialization = highest qualification in NMC records (e.g. MD Cardiology)
