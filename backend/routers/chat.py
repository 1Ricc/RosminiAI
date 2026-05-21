# PLACEHOLDER — verrà implementato in Task 9
from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def chat():
    return {"reply": "Placeholder — AI agent non ancora implementato.", "markers": [], "route": None, "chips": []}
