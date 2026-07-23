"""Tests for the LLM advisor (stub backend)."""
import os
os.environ["LLM_BACKEND"] = "stub"

import pytest
from nepal_decarb_pro.llm.advisor import answer_question, AdvisorContext


@pytest.fixture
def ctx_en():
    return AdvisorContext(
        plant_name="PlantA Industries Ltd",
        plant_type="cement_dry",
        plant_location="PlantA, Makwanpur",
        baseline_2024={"intensity_kg_per_t": 783, "total_tco2": 861025, "clinker_ratio": 0.85},
        intensity_history=[
            {"month": "2024-01", "intensity_kg_per_t": 800},
            {"month": "2024-02", "intensity_kg_per_t": 795},
            {"month": "2024-03", "intensity_kg_per_t": 783},
        ],
        recent_anomalies=[
            {"ts": "2024-03-15", "metric": "CO", "value": 1200, "expected": "<500"},
        ],
        fuel_mix={"coal_bituminous_NP": 0.85, "petcoke": 0.15},
        language="en",
        user_question="Why is my CO2 high?",
    )


@pytest.fixture
def ctx_ne():
    return AdvisorContext(
        plant_name="हेटौंडा सिमेन्ट",
        plant_type="cement_dry",
        plant_location="हेटौंडा, मकवानपुर",
        baseline_2024={"intensity_kg_per_t": 783, "total_tco2": 861025, "clinker_ratio": 0.85},
        intensity_history=[],
        recent_anomalies=[],
        fuel_mix={},
        language="ne",
        user_question="३०% CO2 कम गर्न के गर्ने?",
    )


def test_answer_english(ctx_en):
    resp = answer_question(ctx_en)
    assert resp.answer
    assert "783" in resp.answer or "CO2" in resp.answer
    assert resp.model == "stub"
    assert resp.latency_ms >= 0


def test_answer_nepali(ctx_ne):
    resp = answer_question(ctx_ne)
    assert resp.answer
    # Should have Nepali characters
    assert any("\u0900" <= c <= "\u097f" for c in resp.answer)
    assert resp.model == "stub"


def test_answer_reduce_question(ctx_en):
    ctx_en.user_question = "How do I reduce by 30%?"
    resp = answer_question(ctx_en)
    assert "861,025" in resp.answer or "30%" in resp.answer
    assert "NPV" in resp.answer or "SBTi" in resp.answer


def test_answer_default_question(ctx_en):
    ctx_en.user_question = "Tell me about this plant"
    resp = answer_question(ctx_en)
    assert "861,025" in resp.answer or "783" in resp.answer


def test_rag_sources_included(ctx_en):
    resp = answer_question(ctx_en)
    assert len(resp.sources) >= 3
    assert any("ISO 14064" in s for s in resp.sources)


def test_confidence_set(ctx_en):
    resp = answer_question(ctx_en)
    assert 0 <= resp.confidence <= 1
    # Stub backend should be lower than real LLM
    assert resp.confidence == 0.7


def test_empty_question_rejected():
    """Empty question should still return something (graceful)."""
    ctx = AdvisorContext(
        plant_name="X", plant_type="X", plant_location="X",
        baseline_2024={}, intensity_history=[], recent_anomalies=[],
        fuel_mix={}, language="en", user_question="",
    )
    resp = answer_question(ctx)
    # Stub returns default for any question
    assert resp.answer


def test_anomalies_appear_in_sources(ctx_en):
    """Anomalies should be cited in the response sources."""
    resp = answer_question(ctx_en)
    assert any("sensor" in s.lower() for s in resp.sources)
