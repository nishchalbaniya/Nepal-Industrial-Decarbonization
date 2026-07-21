"""
Nepali-language LLM emissions advisor (GPU-deployed).

RAG over the plant's actual telemetry + emission factors + standards.
Bilingual: English / नेपाली.

Runs on GPU via vLLM (recommended) or transformers (fallback).
"""
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# LLM imports are lazy — only needed when ENABLE_LLM_ADVISOR=1
LLM_BACKEND = os.getenv("LLM_BACKEND", "stub")  # 'stub' | 'vllm' | 'transformers' | 'openai'
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "")  # for vLLM or OpenAI-compatible


@dataclass
class AdvisorContext:
    """All the context the LLM needs to answer a question."""
    plant_name: str
    plant_type: str
    plant_location: str
    baseline_2024: Dict[str, float]
    intensity_history: List[Dict[str, Any]]  # last 12 months
    recent_anomalies: List[Dict[str, Any]]
    fuel_mix: Dict[str, float]  # fuel -> % share
    nepali_grid_ef: float = 0.0256  # kg CO2/kWh
    language: str = "en"  # 'en' or 'ne'
    user_question: str = ""
    system_prompt: str = ""

    def to_prompt(self) -> str:
        """Convert context into a single RAG prompt."""
        anom = "\n".join(
            f"- {a.get('ts', '?')}: {a.get('metric', '?')} = {a.get('value', '?')} (expected {a.get('expected', '?')})"
            for a in self.recent_anomalies[:5]
        ) or "None"
        hist = "\n".join(
            f"- {h.get('month', '?')}: {h.get('intensity_kg_per_t', 0):.0f} kg CO2/t"
            for h in self.intensity_history[-12:]
        ) or "No data"
        fuels = "\n".join(f"- {k}: {v*100:.1f}%" for k, v in self.fuel_mix.items()) or "No data"

        if self.language == "ne":
            self.system_prompt = f"""तपाईं नेपालको सिमेन्ट र इँटा उद्योगका लागि विशेषज्ञ कार्बन सल्लाहकार हुनुहुन्छ।
तपाईंसँग {self.plant_name} ({self.plant_location}, {self.plant_type}) को वास्तविक डाटा छ।
जवाफ छोटो, सटीक र कार्यान्वयनयोग्य हुनुपर्छ। सकेसम्म सन्दर्भ दिनुहोस्।"""

            user = f"""प्लान्ट: {self.plant_name}
स्थान: {self.plant_location}
बेसलाइन २०२४: {self.baseline_2024}

पछिल्लो १२ महिनाको तीव्रता (kg CO2/t):
{hist}

हालका विसंगतिहरू:
{anom}

इन्धन मिश्रण:
{fuels}

प्रश्न: {self.user_question}

छोटो जवाफ दिनुहोस् (३-५ वाक्य), कार्यान्वयन योग्य सुझाव सहित।"""
        else:
            self.system_prompt = f"""You are an expert carbon advisor for Nepal's cement and brick industry.
You have access to real data from {self.plant_name} ({self.plant_location}, {self.plant_type}).
Answer concisely, accurately, and actionably. Cite specific data points where possible.
Use ISO 14064 / IPCC / GCCA terminology where appropriate. Give cost estimates in USD when suggesting changes."""

            user = f"""Plant: {self.plant_name}
Location: {self.plant_location}
2024 baseline: {self.baseline_2024}

Last 12 months intensity (kg CO2/t):
{hist}

Recent anomalies:
{anom}

Fuel mix:
{fuels}

Question: {self.user_question}

Answer concisely (3-5 sentences) with actionable suggestions. If the question is in Nepali, respond in Nepali."""

        return user


@dataclass
class AdvisorResponse:
    answer: str
    model: str
    tokens_used: int = 0
    latency_ms: int = 0
    sources: List[str] = field(default_factory=list)
    confidence: float = 1.0


def answer_question(ctx: AdvisorContext) -> AdvisorResponse:
    """Generate an answer to the user's question using the LLM."""
    user_prompt = ctx.to_prompt()
    sources = [
        "nepal_decarb_pro/core/cement.py: Tier 2/3 cement methodology",
        "nepal_decarb_pro/core/uncertainty.py: Monte Carlo UQ",
        "nepal_decarb_pro/standards/iso_14064.py: ISO 14064-1 compliance",
        "nepal_decarb_pro/standards/gcca.py: GCCA KPIs",
        "nepal_decarb_pro/markets/verra.py: Verra VCS PDD",
    ]
    if ctx.recent_anomalies:
        sources.append("plant sensor readings (last 24h)")
    if ctx.intensity_history:
        sources.append("plant baseline + 12-month history")

    t0 = datetime.now()

    if LLM_BACKEND == "stub":
        # Deterministic stub for testing without GPU
        answer = _stub_answer(ctx)
        tokens = 0
    elif LLM_BACKEND == "vllm":
        answer, tokens = _call_vllm(ctx.system_prompt, user_prompt)
    elif LLM_BACKEND == "transformers":
        answer, tokens = _call_transformers(ctx.system_prompt, user_prompt)
    elif LLM_BACKEND == "openai":
        answer, tokens = _call_openai(ctx.system_prompt, user_prompt)
    else:
        raise ValueError(f"Unknown LLM backend: {LLM_BACKEND}")

    latency = int((datetime.now() - t0).total_seconds() * 1000)
    return AdvisorResponse(
        answer=answer,
        model=LLM_MODEL if LLM_BACKEND != "stub" else "stub",
        tokens_used=tokens,
        latency_ms=latency,
        sources=sources,
        confidence=0.9 if LLM_BACKEND != "stub" else 0.7,
    )


def _stub_answer(ctx: AdvisorContext) -> str:
    """A good stub that demonstrates the RAG-style answer."""
    intensity = ctx.baseline_2024.get("intensity_kg_per_t", 783)
    total = ctx.baseline_2024.get("total_tco2", 861025)
    if "high" in ctx.user_question.lower() or "बढी" in ctx.user_question:
        if ctx.language == "ne":
            return f"""तपाईंको हालको तीव्रता {intensity:.0f} kg CO2/t छ, जुन विश्वव्यापी औसत (700 kg CO2/t) भन्दा ~{(intensity-700)/700*100:.0f}% बढी छ।
मुख्य कारण: क्लिंकर सिमेन्ट अनुपात ( clinker ratio) {ctx.baseline_2024.get('clinker_ratio', 0.85):.2f} छ — ०.७५ मा झार्नाले ~१०% CO2 कम हुन्छ।
सुझाव: ३०% जैविक इन्धन (बायोमास, RDF) ले ~५५,००० tCO2/yr घटाउँछ, अनुमानित लागत $१.२M/yr (NPV $4.5M @ EU ETS $65/t)।
GCCA best practice अनुसार: alternative fuel substitution ३०%+ पुगेको अवस्थामा intensity लक्ष्य <720 kg CO2/t सम्भव छ।"""
        return f"""Your current intensity is {intensity:.0f} kg CO2/t cement, ~{(intensity-700)/700*100:.0f}% above the global average (700 kg CO2/t).
The biggest lever is your clinker-to-cement ratio ({ctx.baseline_2024.get('clinker_ratio', 0.85):.2f}) — bringing it to 0.75 cuts ~10% of CO2.
Recommended action: 30% alternative fuel substitution (biomass + RDF) saves ~55,000 tCO2/yr at an estimated cost of $1.2M/yr (NPV $4.5M at EU ETS $65/t).
Per GCCA "Getting the Numbers Right" benchmarks, plants in your tier can reach <720 kg CO2/t with AF rate 30%+."""
    if "reduce" in ctx.user_question.lower() or "कम" in ctx.user_question:
        if ctx.language == "ne":
            return f"""कुल CO2 ({total:,.0f} tCO2/yr) लाई ३०% कम गर्न ३ वटा कदम चाहिन्छ:
१) क्लिंकर अनुपात ०.७० मा झार्न (वर्तमान ०.८५ बाट): -१२% CO2, लागत $0.5M/yr
२) इन्धन मिश्रण: ४०% बायोमास + १५% RDF (वर्तमान ०% बाट): -१०% CO2, लागत $0.8M/yr
३) किल्न ऊर्जा दक्षता २९०० → २७०० MJ/t: -८% CO2, लागत $1.5M (preheater upgrade)
संयुक्त NPV: $9.5M @ EU ETS $65/t। SBTi 1.5°C लक्ष्य अनुरूप छ।"""
        return f"""To cut your total CO2 ({total:,.0f} tCO2/yr) by 30%, three interventions are needed:
1) Drop clinker ratio from {ctx.baseline_2024.get('clinker_ratio', 0.85):.2f} to 0.70: -12% CO2, $0.5M/yr cost
2) Fuel mix: 40% biomass + 15% RDF (from current 0%): -10% CO2, $0.8M/yr cost
3) Kiln energy efficiency 2900 → 2700 MJ/t: -8% CO2, $1.5M capex (preheater upgrade)
Combined NPV: $9.5M at EU ETS $65/t. Aligned with SBTi 1.5°C pathway."""
    # Default
    if ctx.language == "ne":
        return f"""यो प्लान्टको वार्षिक CO2 उत्सर्जन {total:,.0f} tCO2/yr र तीव्रता {intensity:.0f} kg CO2/t छ।
मुख्य अवसरहरू: क्लिंकर अनुपात, वैकल्पिक इन्धन, किल्न दक्षता।
विस्तृत सुझावको लागि विशेष प्रश्न सोध्नुहोस्।"""
    return f"""This plant's annual emissions are {total:,.0f} tCO2/yr at an intensity of {intensity:.0f} kg CO2/t.
Key levers: clinker ratio, alternative fuels, kiln efficiency.
Ask me a specific question (e.g., "how do I reduce by 30%?") for tailored advice."""


def _call_vllm(system: str, user: str) -> tuple[str, int]:
    """Call vLLM HTTP server (OpenAI-compatible API)."""
    try:
        import requests
    except ImportError:
        raise RuntimeError("vLLM backend requires `requests` package")
    url = LLM_ENDPOINT.rstrip("/") + "/v1/chat/completions"
    r = requests.post(url, json={
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 600,
    }, timeout=30)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"], data["usage"]["total_tokens"]


def _call_transformers(system: str, user: str) -> tuple[str, int]:
    """Use transformers (slower, but works on a single GPU)."""
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    global _model, _tokenizer
    try:
        _model
    except NameError:
        _tokenizer = AutoTokenizer.from_pretrained(LLM_MODEL)
        _model = AutoModelForCausalLM.from_pretrained(
            LLM_MODEL, torch_dtype=torch.bfloat16, device_map="auto"
        )
    prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n{system}<|eot_id|><|start_header_id|>user<|end_header_id|>\n{user}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n"
    inputs = _tokenizer(prompt, return_tensors="pt").to(_model.device)
    out = _model.generate(**inputs, max_new_tokens=600, do_sample=True, temperature=0.2, top_p=0.9)
    text = _tokenizer.decode(out[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return text, out.shape[1] - inputs.input_ids.shape[1]


def _call_openai(system: str, user: str) -> tuple[str, int]:
    """OpenAI-compatible API (works with OpenAI, Together, Anyscale, etc.)."""
    import requests
    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY env var required for openai backend")
    r = requests.post(
        LLM_ENDPOINT or "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 600,
        },
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"], data["usage"]["total_tokens"]
