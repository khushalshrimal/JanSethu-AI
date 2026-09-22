from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.conversation import ConversationRequest, ConversationResponse
from app.services.conversation_manager import ConversationManager

router = APIRouter()

@router.post("/message", response_model=ConversationResponse, summary="Process Stateful Conversation Message")
async def process_conversation_message_endpoint(
    req: ConversationRequest,
    db: Session = Depends(get_db)
):
    """
    Stateful Conversation & Context Management Endpoint for JanSethu AI.
    Processes user message through NLU, updates multi-turn session memory,
    executes real healthcare tools against database, pre-empts emergency safety threats,
    and returns a concise natural assistant response.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message field cannot be empty."
        )

    try:
        response = await ConversationManager.process_message(req, db=db)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing conversation message: {str(e)}"
        )
