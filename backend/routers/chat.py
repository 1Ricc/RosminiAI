from fastapi import APIRouter, Request
from pydantic import BaseModel

from ai.agent import run_agent

router = APIRouter()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
async def chat(req: ChatRequest, request: Request):
    datasets = request.app.state.datasets
    result = await run_agent(req.message, datasets)
    return result
