"""
scraper.py — Direct NMC API call
NMC array format: [sr, year, regNo, council, doctorName, fatherName, viewLink]
"""

import httpx
import re


NMC_API_URL = "https://www.nmc.org.in/MCIRest/open/getPaginatedData"


async def scrape_nmc_portal(registration_number: str, state_council: str) -> dict:
    try:
        return await _call_nmc_api(registration_number, state_council)
    except Exception as e:
        return _not_found(registration_number, state_council, str(e))


async def _call_nmc_api(reg_no: str, state_council: str) -> dict:
    params = {
        "service": "getPaginatedDoctor",
        "draw": "1",
        "start": "0",
        "length": "500",
        "search[value]": "",
        "search[regex]": "false",
        "name": "",
        "registrationNo": reg_no,
        "smcId": "",
        "year": "",
        "order[0][column]": "0",
        "order[0][dir]": "asc",
    }
    for i in range(7):
        params[f"columns[{i}][data]"] = str(i)
        params[f"columns[{i}][name]"] = ""
        params[f"columns[{i}][searchable]"] = "true"
        params[f"columns[{i}][orderable]"] = "true"
        params[f"columns[{i}][search][value]"] = ""
        params[f"columns[{i}][search][regex]"] = "false"

    headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "en-IN,en-GB;q=0.9,en;q=0.8",
        "Referer": "https://www.nmc.org.in/information-desk/indian-medical-register/",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Safari/605.1.15"
        ),
    }

    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(NMC_API_URL, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    doctors = data.get("data", [])
    if not doctors:
        return _not_found(reg_no, state_council, "No record found in NMC registry")

    # Exact match — NMC returns partial matches too
    # Array format: [sr, year, regNo, council, doctorName, fatherName, viewLink]
    doc = None
    for d in doctors:
        if (len(d) > 2
                and str(d[2]).strip().upper() == reg_no.strip().upper()
                and (str(d[3]).strip().upper() == state_council.strip().upper()
     or str(d[3]).strip().upper() in state_council.strip().upper()
     or state_council.strip().upper() in str(d[3]).strip().upper())):
            doc = d
            break

    if doc is None:
        return _not_found(reg_no, state_council, f"No exact match found for registration number '{reg_no}'")

    # Extract doctor ID from view link for detail API
    doctor_id = ""
    if len(doc) > 6:
        match = re.search(r"openDoctorDetailsnew\('(\d+)'", str(doc[6]))
        if match:
            doctor_id = match.group(1)

    result = {
        "verified": True,
        "source": "nmc_portal",
        "doctor_name": str(doc[4]) if len(doc) > 4 else "",
        "registration_number": str(doc[2]) if len(doc) > 2 else reg_no,
        "state_council": str(doc[3]) if len(doc) > 3 else state_council,
        "registration_date": str(doc[1]) if len(doc) > 1 else "",
        "qualifications": ["MBBS"],
        "specialization": "General Practice",
        "status": "Active",
        "father_name": str(doc[5]) if len(doc) > 5 else "",
    }

    # Fetch qualifications from detail page
    if doctor_id:
        detail = await _fetch_doctor_detail(doctor_id, reg_no, headers)
        if detail:
            result["qualifications"] = detail.get("qualifications", ["MBBS"])
            result["specialization"] = detail.get("specialization", "General Practice")
            result["registration_date"] = detail.get("registration_date") or result["registration_date"]
            result["address"] = detail.get("address", "")
    # Check blacklist
    is_blacklisted = await _check_blacklist(reg_no, str(doc[3]) if len(doc) > 3 else state_council)
    if is_blacklisted:
        result["status"] = "Suspended"
        result["blacklisted"] = True
    else:
        result["blacklisted"] = False

    return result


async def _fetch_doctor_detail(doctor_id: str, reg_no: str, headers: dict) -> dict:
    try:
        url = "https://www.nmc.org.in/MCIRest/open/getDataFromService?service=getDoctorDetailsByIdImrExt"
        detail_headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Origin": "https://www.nmc.org.in",
            "Referer": "https://www.nmc.org.in/information-desk/indian-medical-register/",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        }
        payload = {
            "doctorId": doctor_id,
            "regdNoValue": reg_no,
        }
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.post(url, json=payload, headers=detail_headers)
            resp.raise_for_status()
            data = resp.json()

        print(f"Detail response: {str(data)[:500]}")

        qualifications = []
        spec = ""
        reg_date = ""

        if isinstance(data, dict):
            # Primary degree
            primary = data.get("doctorDegree", "")
            if primary and primary.strip():
                qualifications.append(primary.strip())

            # Additional qualifications
            for i in range(1, 4):
                addl = data.get(f"addlqual{i}", "")
                if addl and addl.strip() and addl.strip() not in qualifications:
                    qualifications.append(addl.strip())

            # College info
            college = data.get("college", "")
            university = data.get("university", "")

            spec = data.get("specialization") or data.get("speciality") or ""
            reg_date = data.get("regDate") or data.get("registrationDate", "")

        elif isinstance(data, list) and data:
            d = data[0]
            for key in ["qualificationDetailsList", "qualifications", "qualification"]:
                val = d.get(key)
                if val:
                    if isinstance(val, list):
                        for q in val:
                            name = q.get("qualificationName", "") if isinstance(q, dict) else str(q)
                            if name:
                                qualifications.append(name)
                    else:
                        qualifications.append(str(val))
                    break
            spec = d.get("specialization", "")
            reg_date = d.get("registrationDate", "")

        if not qualifications:
            qualifications = ["MBBS"]
        if not spec:
            spec = _extract_spec(qualifications)

        address = data.get("addressLine1") or data.get("address") or data.get("homeAddress") or ""

        return {"qualifications": qualifications, "specialization": spec, "registration_date": reg_date, "address": address}

    except Exception as e:
        print(f"Detail fetch error: {e}")
        return {}


async def _check_blacklist(reg_no: str, council: str) -> bool:
    try:
        url = "https://www.nmc.org.in/MCIRest/open/getDataFromService?service=getBlackListedDoctors"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Referer": "https://www.nmc.org.in/information-desk/indian-medical-register/black-list-doctors/",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://www.nmc.org.in",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15",
        }
        payload = {
            "smcs": "",
            "regnNo": reg_no,
            "suspendDate": "",
            "restorDate": "",
        }
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        print(f"Blacklist response: {str(data)[:300]}")

        # Agar list mein kuch aaya toh blacklisted hai
        if isinstance(data, list) and len(data) > 0:
            return True
        if isinstance(data, dict) and data.get("data") and len(data["data"]) > 0:
            return True
        return False

    except Exception as e:
        print(f"Blacklist check error: {e}")
        return False

    except Exception as e:
        print(f"Blacklist check error: {e}")
        return False


def _extract_spec(qualifications: list) -> str:
    if not qualifications:
        return "General Practice (MBBS)"
    for q in reversed(qualifications):
        if any(x in q.upper() for x in ["DM", "MCH", "DNB", "FELLOWSHIP"]):
            return q
        if any(x in q.upper() for x in ["MD", "MS", "MDS"]):
            return q
    return qualifications[-1]


def _not_found(reg_no: str, state: str, reason: str) -> dict:
    return {
        "verified": False,
        "source": "nmc_portal",
        "registration_number": reg_no,
        "state_council": state,
        "error": (
            f"Doctor not found ({reason}). "
            "Please verify manually at: "
            "https://www.nmc.org.in/information-desk/indian-medical-register/"
        ),
    }