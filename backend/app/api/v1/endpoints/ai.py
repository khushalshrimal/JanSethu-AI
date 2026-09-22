from fastapi import APIRouter, HTTPException, status
from app.schemas.nlu import NLUAnalysisRequest, NLUAnalysisResponse
from app.services.llm_service import LLMService

router = APIRouter()

@router.post("/analyze", response_model=NLUAnalysisResponse, summary="Analyze Natural Language Message (NLU)")
async def analyze_message_endpoint(req: NLUAnalysisRequest):
    """
    Public NLU Analysis Endpoint for JanSethu AI.
    Processes natural language input in English, Hindi, Hinglish, or Marathi.
    Runs deterministic emergency safety check followed by LLM / NLU intent parsing and multi-entity extraction.
    Does NOT mutate database or execute healthcare booking actions.
    """
    if not req.message or not req.message.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message field cannot be empty."
        )

    response = await LLMService.analyze_nlu(
        message=req.message,
        conversation_context=req.conversation_context,
        language_hint=req.language_hint
    )
    return response
