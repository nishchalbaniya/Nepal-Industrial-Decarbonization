"""LLM-powered Nepali emissions advisor (GPU-deployed)."""
from .advisor import answer_question, AdvisorContext, AdvisorResponse

# Lazy import: serve.py needs FastAPI which may not be installed in CLI usage
def __getattr__(name):
    if name == "advisor_router":
        from .serve import router as advisor_router
        return advisor_router
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["answer_question", "AdvisorContext", "AdvisorResponse", "advisor_router"]
