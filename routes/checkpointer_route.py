from fastapi import APIRouter, HTTPException
from repos.checkpointer import async_memory , CheckpointerService

router = APIRouter(prefix="/cp", tags=["Checkpointer Routes"])

@router.get("/latest_checkpoint")
async def get_latest_checkpoint(thread_id: str, user_email: str):
    config = {
        "configurable": {
            "thread_id": thread_id,
            "user_email": user_email
        }
    }
    try:
        latest_checkpoint = await async_memory.aget(config)
        if latest_checkpoint is None:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        return latest_checkpoint
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
@router.get("/get_recent_threads")
async def get_recent_threads():
    try:
        result = await CheckpointerService.get_recent_threads()
        if not result:
            raise HTTPException(status_code=404, detail="No valid thread entries found")
        return {"recent_threads": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest_checkpoint_qa")
async def get_latest_checkpoint_qa(thread_id: str, user_email: str):
    try:
        result = await CheckpointerService.get_latest_checkpoint_qa(thread_id, user_email)
        if result is None:
            raise HTTPException(status_code=404, detail="Checkpoint not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
