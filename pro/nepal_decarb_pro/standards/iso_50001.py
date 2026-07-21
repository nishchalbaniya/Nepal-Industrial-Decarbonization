"""
ISO 50001:2018 — Energy Management Systems.

Implements the EnPI (Energy Performance Indicator) framework and Plan-Do-Check-Act
cycle for cement and brick plants.
"""
from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class ISO50001Result(BaseModel):
    """Result of an ISO 50001 compliance check."""
    pass_: bool
    score: float
    criteria: List[Dict]
    energy_review_complete: bool
    enpis_defined: List[str]
    energy_baseline_set: bool
    objectives_targets_set: bool
    energy_action_plan: bool
    monitoring_system: bool
    management_review: bool
    notes: str = ""


def check_iso_50001(
    plant_name: str,
    energy_review_complete: bool = True,
    enpis_defined: Optional[List[str]] = None,
    energy_baseline_set: bool = True,
    objectives_targets_set: bool = True,
    energy_action_plan: bool = True,
    monitoring_system: bool = True,
    management_review: bool = True,
) -> ISO50001Result:
    """Check ISO 50001 energy management compliance."""
    if enpis_defined is None:
        enpis_defined = [
            "Specific energy consumption (MJ/t clinker)",
            "Specific power consumption (kWh/t cement)",
            "Alternative fuel substitution rate (%)",
            "WHR generation (kWh/yr)",
        ]
    criteria = [
        {"id": "4.1", "name": "Context of organization", "met": True},
        {"id": "4.2", "name": "Leadership", "met": True},
        {"id": "5.1", "name": "Planning — General", "met": True},
        {"id": "5.2", "name": "Planning — Energy review", "met": energy_review_complete},
        {"id": "5.3", "name": "Planning — EnPIs", "met": len(enpis_defined) >= 1},
        {"id": "5.4", "name": "Planning — Energy baseline", "met": energy_baseline_set},
        {"id": "5.5", "name": "Planning — Objectives & targets", "met": objectives_targets_set},
        {"id": "5.6", "name": "Planning — Action plan", "met": energy_action_plan},
        {"id": "6.1", "name": "Support", "met": True},
        {"id": "6.2", "name": "Competence", "met": True},
        {"id": "6.3", "name": "Awareness", "met": True},
        {"id": "6.4", "name": "Communication", "met": True},
        {"id": "6.5", "name": "Documented information", "met": True},
        {"id": "7.1", "name": "Operation — General", "met": True},
        {"id": "7.2", "name": "Operation — Energy planning", "met": True},
        {"id": "7.3", "name": "Operation — Monitoring & measurement", "met": monitoring_system},
        {"id": "8.1", "name": "Performance evaluation", "met": True},
        {"id": "8.2", "name": "Evaluation of compliance", "met": True},
        {"id": "8.3", "name": "Internal audit", "met": True},
        {"id": "9.1", "name": "Nonconformity & corrective action", "met": True},
        {"id": "9.2", "name": "Management review", "met": management_review},
        {"id": "9.3", "name": "Continual improvement", "met": True},
    ]
    n_met = sum(1 for c in criteria if c["met"])
    score = 100.0 * n_met / len(criteria) if criteria else 100
    return ISO50001Result(
        pass_=all(c["met"] for c in criteria),
        score=score,
        criteria=criteria,
        energy_review_complete=energy_review_complete,
        enpis_defined=enpis_defined,
        energy_baseline_set=energy_baseline_set,
        objectives_targets_set=objectives_targets_set,
        energy_action_plan=energy_action_plan,
        monitoring_system=monitoring_system,
        management_review=management_review,
        notes=f"EnPIs: {', '.join(enpis_defined)}",
    )
