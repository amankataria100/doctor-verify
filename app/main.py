from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.verifier import verify_doctor
import uvicorn

app = FastAPI(title="Doctor Verification API")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


class VerifyRequest(BaseModel):
    registration_number: str
    state_council: str
    year_of_admission: str = ""   # optional, needed for Surepass


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/verify")
async def verify(data: VerifyRequest):
    if not data.registration_number.strip():
        raise HTTPException(status_code=400, detail="Registration number required")
    if not data.state_council.strip():
        raise HTTPException(status_code=400, detail="State council required")

    result = await verify_doctor(
        registration_number=data.registration_number.strip().upper(),
        state_council=data.state_council.strip(),
        year_of_admission=data.year_of_admission.strip(),
    )
    return JSONResponse(content=result)


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
