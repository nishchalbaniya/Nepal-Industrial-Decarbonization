"""
ISO 14001:2015 — Environmental Management Systems.
"""
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel, Field
from datetime import datetime


class ISO14001Result(BaseModel):
    pass_: bool
    score: float
    criteria: List[Dict]
    ems_documented: bool
    aspects_identified: List[str]
    legal_compliance: bool
    objectives_targets: bool
    monitoring_measurement: bool
    notes: str = ""


def check_iso_14001(
    plant_name: str,
    ems_documented: bool = True,
    aspects_identified: Optional[List[str]] = None,
    legal_compliance: bool = True,
    objectives_targets: bool = True,
    monitoring_measurement: bool = True,
) -> ISO14001Result:
    if aspects_identified is None:
        aspects_identified = [
            "CO2 emissions (climate change)",
            "Particulate matter (air quality)",
            "NOx emissions (air quality)",
            "Water consumption (water stress)",
            "Solid waste (clinker dust, refractories)",
            "Noise (community impact)",
        ]
    criteria = [
        {"id": "4.1", "name": "Context of organization", "met": True},
        {"id": "4.2", "name": "Needs & expectations", "met": True},
        {"id": "4.3", "name": "Scope of EMS", "met": ems_documented},
        {"id": "4.4", "name": "EMS", "met": ems_documented},
        {"id": "5.1", "name": "Leadership & commitment", "met": True},
        {"id": "5.2", "name": "Environmental policy", "met": True},
        {"id": "5.3", "name": "Roles & responsibilities", "met": True},
        {"id": "6.1.1", "name": "Environmental aspects", "met": len(aspects_identified) >= 1},
        {"id": "6.1.2", "name": "Compliance obligations", "met": legal_compliance},
        {"id": "6.1.3", "name": "Risks & opportunities", "met": True},
        {"id": "6.1.4", "name": "Environmental objectives", "met": objectives_targets},
        {"id": "6.2", "name": "Planning of actions", "met": objectives_targets},
        {"id": "7.1", "name": "Resources", "met": True},
        {"id": "7.2", "name": "Competence", "met": True},
        {"id": "7.3", "name": "Awareness", "met": True},
        {"id": "7.4", "name": "Communication", "met": True},
        {"id": "7.5", "name": "Documented information", "met": True},
        {"id": "8.1", "name": "Operational planning", "met": True},
        {"id": "8.2", "name": "Emergency preparedness", "met": True},
        {"id": "9.1.1", "name": "Monitoring & measurement", "met": monitoring_measurement},
        {"id": "9.1.2", "name": "Evaluation of compliance", "met": legal_compliance},
        {"id": "9.2", "name": "Internal audit", "met": True},
        {"id": "9.3", "name": "Management review", "met": True},
        {"id": "10.1", "name": "Nonconformity & corrective action", "met": True},
        {"id": "10.2", "name": "Continual improvement", "met": True},
    ]
    n_met = sum(1 for c in criteria if c["met"])
    score = 100.0 * n_met / len(criteria) if criteria else 100
    return ISO14001Result(
        pass_=all(c["met"] for c in criteria),
        score=score,
        criteria=criteria,
        ems_documented=ems_documented,
        aspects_identified=aspects_identified,
        legal_compliance=legal_compliance,
        objectives_targets=objectives_targets,
        monitoring_measurement=monitoring_measurement,
        notes=f"{len(aspects_identified)} environmental aspects identified",
    )
