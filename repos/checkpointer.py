import os
from bson.binary import Binary
from langgraph.checkpoint.mongodb import AsyncMongoDBSaver
from config import aclient
import json
# Initialize checkpointers
async_memory = AsyncMongoDBSaver(
    client=aclient,
    db_name= os.environ["DATABASE_NAME"]
)

# Database collections
db = aclient[os.environ["DATABASE_NAME"]]
checkpoint_collection = db["checkpoints_aio"]
checkpointWrites_collection = db["checkpoint_writes_aio"]


class CheckpointerService:
    
    @staticmethod
    async def get_latest_checkpoint(thread_id: str, user_email: str):
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_email": user_email
            }
        }
        checkpoint = await async_memory.aget(config)
        if not checkpoint:
            return None
            
       
        messages = checkpoint.get("channel_values", {}).get("messages", [])
        simple_messages = []
        
        for msg in messages:
            
            try:
                msg_type = getattr(msg, 'type', 'unknown')
                content = getattr(msg, 'content', '')
                tool_calls = getattr(msg, 'tool_calls', [])
            except:
                # Fallback for dict-like objects
                msg_type = msg.get('type', 'unknown') if isinstance(msg, dict) else 'unknown'
                content = msg.get('content', '') if isinstance(msg, dict) else str(msg)
                tool_calls = msg.get('tool_calls', []) if isinstance(msg, dict) else []
            
            simple_messages.append({
                "type": msg_type,
                "content": content[:200] + "..." if len(str(content)) > 200 else str(content),
                "tool_calls": len(tool_calls) > 0
            })
        
        return {
            "thread_id": thread_id,
            "timestamp": checkpoint.get("ts"),
            "messages": simple_messages,
            "total_messages": len(messages)
        }


    @staticmethod
    async def get_recent_threads():
        # Debug: Check what collections exist
        collections = await db.list_collection_names()
        print(collections)
        # Debug: Count documents in checkpoint collections
        checkpoint_count = await checkpoint_collection.count_documents({})
        checkpoint_writes_count = await checkpointWrites_collection.count_documents({})
        
        # Get recent threads using simple find
        result = []
        seen_threads = set()
        
        cursor = checkpoint_collection.find().sort("_id", -1).limit(50)
        async for doc in cursor:
            metadata = doc.get("metadata", {}) if isinstance(doc, dict) else {}
            thread_id = doc.get("thread_id")
            raw_email = (
                metadata.get("user_email")
                or doc.get("user_email")
                or doc.get("email")
            )

            email = normalize_email(raw_email)

            if thread_id and thread_id not in seen_threads:
                seen_threads.add(thread_id)
                result.append({
                    "thread_id": thread_id,
                    "email": email
                })
                if len(result) >= 10:
                    break
        
        return {
            "recent_threads": result,
            "total_threads": len(result),
            "database_info": {
                "database": os.environ["DATABASE_NAME"],
                "total_checkpoints": checkpoint_count
            }
        
        }

    @staticmethod
    async def get_latest_checkpoint_qa(thread_id: str, user_email: str):
        config = {
            "configurable": {
                "thread_id": thread_id,
                "user_email": user_email
            }
        }
        checkpoint = await async_memory.aget(config)
        if not checkpoint:
            return None

        messages = checkpoint.get("channel_values", {}).get("messages", [])
        qa_pairs = []
        current_question = None

        for msg in messages:
            if isinstance(msg, dict):
                msg_type = msg.get("type")
                content = msg.get("content")
                tool_calls = msg.get("tool_calls", [])
            else:
                msg_type = getattr(msg, "type", None)
                content = getattr(msg, "content", None)
                tool_calls = getattr(msg, "tool_calls", [])

            if isinstance(content, list):
                if content and isinstance(content[0], dict):
                    text = content[0].get("text") or content[0].get("content") or ""
                else:
                    text = str(content[0]) if content else ""
            elif isinstance(content, dict):
                text = content.get("text") or content.get("content") or ""
            else:
                text = str(content or "")

            if msg_type == "human":
                current_question = text
            elif msg_type == "ai":
                if tool_calls:
                    continue
                if current_question:
                    qa_pairs.append({
                        "question": current_question,
                        "answer": text
                    })
                    current_question = None

        return {
            "thread_id": thread_id,
            "user_email": user_email,
            "qa_pairs": qa_pairs
        }

def normalize_email(raw):
    if raw is None:
        return None
    # bytes / Binary
    if isinstance(raw, (bytes, bytearray)):
        s = raw.decode("utf-8", errors="ignore")
    elif isinstance(raw, Binary):
        s = bytes(raw).decode("utf-8", errors="ignore")
    # lists: take first element
    elif isinstance(raw, (list, tuple)) and raw:
        return normalize_email(raw[0])
    # dicts: try common keys
    elif isinstance(raw, dict):
        for k in ("user_email", "email", "value", "address"):
            if k in raw and raw[k] is not None:
                return normalize_email(raw[k])
        # fallback to string representation
        s = json.dumps(raw) if raw else ""
    else:
        s = str(raw)

    s = s.strip()
    # remove surrounding quotes if present
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()

    if s.lower() in ("none", "null", ""):
        return None
    return s


