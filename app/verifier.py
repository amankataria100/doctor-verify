"""
verifier.py
-----------
Tries sources in order:
  1. Surepass NMC Verification API  (set SUREPASS_TOKEN in .env)
  2. IDfy RapidAPI                  (set RAPIDAPI_KEY in .env)
  3. NMC portal scraper             (free, no key needed — fallback)
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv
from app.scraper import scrape_nmc_portal

load_dotenv()

SUREPASS_TOKEN  = os.getenv("SUREPASS_TOKEN", "")   # from surepass.io
RAPIDAPI_KEY    = os.getenv("RAPIDAPI_KEY", "")      # from rapidapi.com


async def verify_doctor(registration_number: str,
                        state_council: str,
                        year_of_admission: str) -> dict:

    # --- Source 1: Surepass ---
    if SUREPASS_TOKEN:
        result = await scrape_nmc_portal(registration_number, state_council, year_of_admission)
        if result.get("verified"):
            return result

    # --- Source 2: IDfy via RapidAPI ---
    if RAPIDAPI_KEY:
        result = await _idfy_verify(registration_number, state_council)
        if result.get("verified"):
            return result

    # --- Source 3: NMC Portal Scraper (always runs as fallback) ---
    result = await scrape_nmc_portal(registration_number, state_council, year_of_admission)
    return result


# ──────────────────────────────────────────────
# SOURCE 1 — Surepass NMC Verification API
# Docs: https://surepass.io/nmc-verification-api/
# ──────────────────────────────────────────────
async def _surepass_verify(reg_no: str, state_council: str, year: str) -> dict:
    url = "https://kyc-api.surepass.io/api/v1/nmc/nmc-verification"
    headers = {
        "Authorization": f"Bearer {SUREPASS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "id_number": reg_no,
        "state_council": state_council,
        "year_of_admission": year,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        # Surepass wraps response in data.data
        d = data.get("data", {})
        if not d:
            return {"verified": False, "source": "surepass", "error": "No data returned"}

        return {
            "verified": True,
            "source": "surepass",
            "doctor_name": d.get("full_name") or d.get("name", ""),
            "registration_number": d.get("registration_no", reg_no),
            "state_council": d.get("state_council", state_council),
            "registration_date": d.get("registration_date") or d.get("date_of_registration", ""),
            "qualifications": d.get("qualification", []),
            "specialization": _extract_specialization(d.get("qualification", [])),
            "status": d.get("status", "active"),
            "raw": d,
        }

    except httpx.HTTPStatusError as e:
        return {"verified": False, "source": "surepass", "error": str(e)}
    except Exception as e:
        return {"verified": False, "source": "surepass", "error": str(e)}


# ──────────────────────────────────────────────
# SOURCE 2 — IDfy MCI/NMC via RapidAPI
# Signup: https://rapidapi.com/idfy-idfy-default/api/mci-nmc-doctor-verification
# ──────────────────────────────────────────────
async def _idfy_verify(reg_no: str, state_council: str) -> dict:
    url = "https://mci-nmc-doctor-verification.p.rapidapi.com/v3/tasks/sync/verify_with_source/ind_medical_council"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": "mci-nmc-doctor-verification.p.rapidapi.com",
        "Content-Type": "application/json",
    }
    payload = {
        "task_id": f"verify_{reg_no}",
        "group_id": "doctor_verify",
        "data": {
            "registration_number": reg_no,
            "state_medical_council": state_council,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        result = data.get("result", {})
        source_output = result.get("source_output", {})

        if not source_output:
            return {"verified": False, "source": "idfy", "error": "Doctor not found"}

        qualifications = source_output.get("qualifications", [])

        return {
            "verified": True,
            "source": "idfy",
            "doctor_name": source_output.get("full_name", ""),
            "registration_number": source_output.get("registration_number", reg_no),
            "state_council": source_output.get("state_council", state_council),
            "registration_date": source_output.get("registration_date", ""),
            "qualifications": qualifications,
            "specialization": _extract_specialization(qualifications),
            "status": source_output.get("status", "active"),
            "raw": source_output,
        }

    except httpx.HTTPStatusError as e:
        return {"verified": False, "source": "idfy", "error": str(e)}
    except Exception as e:
        return {"verified": False, "source": "idfy", "error": str(e)}


# ──────────────────────────────────────────────
# HELPER — extract specialization from qualifications list
# ──────────────────────────────────────────────
def _extract_specialization(qualifications) -> str:
    """
    Qualifications can be a list of strings like:
    ["MBBS", "MD (Cardiology)", "DM (Interventional Cardiology)"]
    or a list of dicts. We return the highest/most specific qualification.
    """
    if not qualifications:
        return "General Practice (MBBS)"

    # if list of dicts
    if isinstance(qualifications[0], dict):
        quals = [q.get("qualification", "") or q.get("name", "") for q in qualifications]
    else:
        quals = list(qualifications)

    # Filter out blank
    quals = [q for q in quals if q]

    # Priority order for specialization
    for q in reversed(quals):   # last = highest degree
        upper = q.upper()
        if any(x in upper for x in ["DM", "MCH", "DNB", "FELLOWSHIP"]):
            return q   # super-specialty
        if any(x in upper for x in ["MD", "MS", "MDS", "DIPLOMA"]):
            return q   # post-grad

    return quals[-1] if quals else "MBBS"
