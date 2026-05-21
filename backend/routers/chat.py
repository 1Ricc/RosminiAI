from fastapi import APIRouter

router = APIRouter()


@router.post("/chat")
async def chat():
    # stub — implementazione completa nel Task 9
    return {"reply": "Coming soon", "markers": [], "route": None, "chips": []}
