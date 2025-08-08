# api/routes/agent.py

# imports
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta
from api.auth.deps import get_current_user
from api.crew.agent_handler import run_discern_agents
from api.db.database import get_database
from api.models.message import SendMessageInput
import anyio  # <-- for non-blocking thread offload

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/send-message")
async def send_message(body: SendMessageInput, user=Depends(get_current_user)):
    # connect to db
    db = await get_database()

    # extract input
    user_input = body.content
    conversation_id = body.conversation_id

    # validate content
    if not user_input:
        raise HTTPException(status_code=400, detail="Prompt is required.")

    # deny unsubscribed
    if user.get("role") == "unsubscribed":
        raise HTTPException(status_code=403, detail="Subscription required.")

    # compute limits
    now = datetime.utcnow()
    if user.get("role") == "trial":
        start_time = now - timedelta(days=1)
        max_messages = 25
    elif user.get("role") != "admin":
        start_time = now - timedelta(hours=1)
        max_messages = 25
    else:
        start_time = None
        max_messages = None

    # enforce rate limits for non-admins
    if max_messages is not None:
        recent_count = await db.messages.count_documents({
            "user_id": str(user["_id"]),
            "role": "user",
            "created_at": {"$gte": start_time}
        })
        if recent_count >= max_messages:
            raise HTTPException(status_code=429, detail="Message limit reached. Please wait before sending more.")

    # fetch prior messages if conversation exists
    messages = []
    if not conversation_id:
        # create conversation
        topic = "TBD"  # TODO: replace with topic selector agent
        conversation_doc = {
            "user_id": str(user["_id"]),
            "topic": topic,
            "created_at": now
        }
        result = await db.conversations.insert_one(conversation_doc)
        conversation_id = str(result.inserted_id)
    else:
        # get last 10 messages
        existing = await db.messages.find(
            {"conversation_id": conversation_id}
        ).sort("created_at", -1).limit(10).to_list(length=10)
        messages = list(reversed(existing))

    # fetch up to 20 memories
    memories = await db.memories.find(
        {"user_id": str(user["_id"])}
    ).limit(20).to_list(length=20)

    # save user message
    user_msg_doc = {
        "conversation_id": conversation_id,
        "user_id": str(user["_id"]),
        "role": "user",
        "message": user_input,
        "created_at": now
    }
    await db.messages.insert_one(user_msg_doc)

    # build agent context
    context = {
        "user_input": user_input,
        "user_data": user,
        "conversation": messages,
        "memories": memories
    }

    # --- Non-blocking agent execution ---
    # Run the synchronous run_discern_agents(...) in a worker thread so we don't block the event loop.
    agent_response = await anyio.to_thread.run_sync(run_discern_agents, context)

    # save agent response
    system_msg_doc = {
        "conversation_id": conversation_id,
        "user_id": str(user["_id"]),
        "role": "system",
        "message": agent_response,
        "created_at": datetime.utcnow()
    }
    await db.messages.insert_one(system_msg_doc)

    # return payload
    return {"response": agent_response, "conversation_id": conversation_id}
