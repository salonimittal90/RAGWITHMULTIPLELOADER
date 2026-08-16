# routes/rag_route.py (modified)
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from repos.rag_pipe import async_graph
from langchain_core.messages import HumanMessage
import traceback

router = APIRouter(prefix="/ai", tags=["GraphAI Routes"])

class QuestionRequest(BaseModel):
    question: str
    thread_id: str
    user_email: str

@router.post("/ask_question")
async def get_content(request: QuestionRequest):
    try:
        config = {
            "configurable": {
                "thread_id": request.thread_id,
                "user_email": request.user_email,
            },
            "metadata": {"user_email": request.user_email}
        }

        print("DEBUG before async_graph.ainvoke")
        response = await async_graph.ainvoke(
            {"messages": [HumanMessage(content=request.question)]},
            config
        )

        if not response or not isinstance(response, dict):
            raise HTTPException(
                status_code=500,
                detail=f"Invalid graph response: {response!r}"
            )

        messages = response.get("messages")
        if not messages:
            raise HTTPException(
                status_code=500,
                detail=f"Graph returned no messages: {response!r}"
            )

        last_message = messages[-1]
        content = last_message.content
        if isinstance(content, list) and content:
            content = content[0].get("text") if isinstance(content[0], dict) else str(content[0])

        return {
            "thread_id": request.thread_id,
            "user_email": request.user_email,
            "content": content or "No answer generated."

        }

    except Exception as e:
        print("DEBUG async_graph exception:", type(e).__name__, e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
