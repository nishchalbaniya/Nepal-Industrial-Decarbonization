"""
FastAPI router for the LLM advisor (GPU-deployed).
"""
from __future__ import annotations

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from .advisor import answer_question, AdvisorContext, AdvisorResponse

router = APIRouter(prefix="/api/v1/advisor", tags=["advisor"])


class QuestionRequest(BaseModel):
    plant_name: str
    plant_type: str
    plant_location: str
    baseline_2024: Dict[str, float]
    intensity_history: List[Dict[str, Any]] = Field(default_factory=list)
    recent_anomalies: List[Dict[str, Any]] = Field(default_factory=list)
    fuel_mix: Dict[str, float] = Field(default_factory=dict)
    language: str = "en"
    question: str


class QuestionResponse(BaseModel):
    answer: str
    model: str
    tokens_used: int
    latency_ms: int
    sources: List[str]
    confidence: float


@router.post("/ask", response_model=QuestionResponse)
async def ask_advisor(req: QuestionRequest) -> QuestionResponse:
    """Ask the LLM advisor a question about a plant."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    if req.language not in ("en", "ne"):
        raise HTTPException(status_code=400, detail="language must be 'en' or 'ne'")

    ctx = AdvisorContext(
        plant_name=req.plant_name,
        plant_type=req.plant_type,
        plant_location=req.plant_location,
        baseline_2024=req.baseline_2024,
        intensity_history=req.intensity_history,
        recent_anomalies=req.recent_anomalies,
        fuel_mix=req.fuel_mix,
        language=req.language,
        user_question=req.question,
    )
    resp = answer_question(ctx)
    return QuestionResponse(
        answer=resp.answer,
        model=resp.model,
        tokens_used=resp.tokens_used,
        latency_ms=resp.latency_ms,
        sources=resp.sources,
        confidence=resp.confidence,
    )


@router.get("/example-questions")
async def example_questions(language: str = "en") -> Dict[str, Any]:
    """Return example questions to help users get started."""
    if language == "ne":
        return {
            "questions": [
                "मेरो CO2 उत्सर्जन किन बढी छ?",
                "३०% CO2 कम गर्न के गर्ने?",
                "वैकल्पिक इन्धन प्रयोग गर्दा कति बचत हुन्छ?",
                "SBTi लक्ष्यमा पुग्न मलाई कति वर्ष लाग्छ?",
                "Verra कार्बन क्रेडिटबाट कति आम्दानी हुन्छ?",
            ]
        }
    return {
        "questions": [
            "Why are my CO2 emissions higher than the global average?",
            "How do I reduce emissions by 30%?",
            "What savings can I get from alternative fuels?",
            "How long will it take me to meet SBTi targets?",
            "How much revenue can I get from Verra carbon credits?",
            "Explain my last 3 anomalies in simple terms.",
        ]
    }
