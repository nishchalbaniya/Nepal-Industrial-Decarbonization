"""
FastAPI backend — REST + WebSocket for real-time monitoring.
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn

from nepal_decarb_pro.core.cement import CementPlant, FuelUse, calculate_cement_tier2, calculate_cement_tier3
from nepal_decarb_pro.core.brick import BrickKiln, calculate_brick_emissions
from nepal_decarb_pro.core.factors import default_factors
from nepal_decarb_pro.standards.iso_14064 import check_iso_14064_part1


app = FastAPI(
    title="Nepal Decarbonization API",
    description="World-class industrial decarbonization API for Nepal's cement & brick industry",
    version="1.0.0",
    contact={
        "name": "Nishchal Baniya",
        "email": "nishchal.baniya@himalayancarbonnepal.com",
    },
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------------
# Models
# ----------------------------------------------------------------------------

class CementPlantAPI(BaseModel):
    name: str
    location: str
    year: int
    clinker_production_t: float
    cement_production_t: float
    cao_fraction_clinker: Optional[float] = None
    mgo_fraction_clinker: Optional[float] = None
    coal_t: float = 0
    petcoke_t: float = 0
    diesel_t: float = 0
    electricity_consumption_kwh: float = 0
    whr_generation_kwh: float = 0
    transport_tkm: float = 0


class BrickKilnAPI(BaseModel):
    name: str
    location: str
    year: int
    kiln_type: str
    annual_brick_production: float
    coal_t: Optional[float] = None
    biomass_t: Optional[float] = None
    electricity_consumption_kwh: float = 0


# ----------------------------------------------------------------------------
# Endpoints
# ----------------------------------------------------------------------------

@app.get("/")
def root() -> Dict:
    return {
        "name": "Nepal Decarbonization API",
        "version": "1.0.0",
        "author": "Nishchal Baniya, Himalayan Carbon Nepal",
        "email": "nishchal.baniya@himalayancarbonnepal.com",
        "license": "MIT",
        "standards": [
            "IPCC 2006 Tier 2/3",
            "GHG Protocol Corporate",
            "ISO 14064-1:2018",
            "ISO 14064-2:2019",
            "ISO 14064-3:2019",
            "TCFD",
            "SBTi",
            "GCCA",
            "PCAF",
            "Verra VCS",
            "Gold Standard",
        ],
    }


@app.get("/health")
def health() -> Dict:
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/kiln-types")
def kiln_types() -> List[str]:
    ef = default_factors()
    return list(ef.brick_kilns.keys())


@app.get("/fuels")
def fuels() -> List[Dict]:
    ef = default_factors()
    return [
        {
            "name": k,
            "category": f.category,
            "ncvc_gj_per_t": f.ncvc_gj_per_t,
            "ef_kgco2_per_gj": f.ef_kgco2_per_gj,
            "biogenic_fraction": f.biogenic_fraction,
            "price_usd_per_t": f.price_usd_per_t,
        }
        for k, f in ef.fuels.items()
    ]


@app.post("/cement/calculate", response_model=Dict)
def calculate_cement(plant_data: CementPlantAPI, tier: int = 2) -> Dict:
    """Calculate cement baseline emissions. tier=2 (default) or tier=3."""
    ef = default_factors()
    fuels = []
    if plant_data.coal_t > 0:
        fuels.append(FuelUse(fuel_name="coal_bituminous_NP", consumption_t=plant_data.coal_t))
    if plant_data.petcoke_t > 0:
        fuels.append(FuelUse(fuel_name="petcoke", consumption_t=plant_data.petcoke_t))
    if plant_data.diesel_t > 0:
        fuels.append(FuelUse(fuel_name="diesel", consumption_t=plant_data.diesel_t))

    plant = CementPlant(
        name=plant_data.name,
        location=plant_data.location,
        year=plant_data.year,
        clinker_production_t=plant_data.clinker_production_t,
        cement_production_t=plant_data.cement_production_t,
        cao_fraction_clinker=plant_data.cao_fraction_clinker,
        mgo_fraction_clinker=plant_data.mgo_fraction_clinker,
        fuel_use=fuels,
        electricity_consumption_kwh=plant_data.electricity_consumption_kwh,
        whr_generation_kwh=plant_data.whr_generation_kwh,
        transport_tkm=plant_data.transport_tkm,
    )

    if tier == 3:
        result = calculate_cement_tier3(plant, ef)
    else:
        result = calculate_cement_tier2(plant, ef)
    return result.model_dump()


@app.post("/brick/calculate")
def calculate_brick(kiln_data: BrickKilnAPI) -> Dict:
    """Calculate brick kiln baseline emissions."""
    ef = default_factors()
    if kiln_data.kiln_type not in ef.brick_kilns:
        raise HTTPException(400, f"Unknown kiln type. Available: {list(ef.brick_kilns)}")

    fuels = []
    if kiln_data.coal_t is not None:
        fuels.append(FuelUse(fuel_name="coal_bituminous_NP", consumption_t=kiln_data.coal_t))
    if kiln_data.biomass_t is not None:
        fuels.append(FuelUse(fuel_name="biomass_rice_husk", consumption_t=kiln_data.biomass_t))

    kiln = BrickKiln(
        name=kiln_data.name,
        location=kiln_data.location,
        year=kiln_data.year,
        kiln_type=kiln_data.kiln_type,
        annual_brick_production=kiln_data.annual_brick_production,
        fuel_use=fuels,
        electricity_consumption_kwh=kiln_data.electricity_consumption_kwh,
    )
    result = calculate_brick_emissions(kiln, ef)
    return result.model_dump()


@app.post("/iso-14064-1/check")
def iso_check(plant_data: CementPlantAPI) -> Dict:
    """Check ISO 14064-1 compliance for a cement plant."""
    ef = default_factors()
    fuels = [
        FuelUse(fuel_name="coal_bituminous_NP", consumption_t=plant_data.coal_t),
        FuelUse(fuel_name="petcoke", consumption_t=plant_data.petcoke_t),
    ]
    plant = CementPlant(
        name=plant_data.name, location=plant_data.location, year=plant_data.year,
        clinker_production_t=plant_data.clinker_production_t,
        cement_production_t=plant_data.cement_production_t,
        fuel_use=fuels, electricity_consumption_kwh=plant_data.electricity_consumption_kwh,
    )
    cement_result = calculate_cement_tier2(plant, ef)
    iso_result = check_iso_14064_part1(
        plant=plant,
        cement_result=cement_result,
    )
    return iso_result.model_dump()


# WebSocket for real-time
@app.websocket("/ws/realtime")
async def websocket_realtime(websocket: WebSocket) -> None:
    """Real-time data stream from IoT sensors."""
    await websocket.accept()
    try:
        while True:
            # Receive data
            data = await websocket.receive_text()
            # Process
            response = {"echo": data, "timestamp": "2026-07-21T00:00:00"}
            await websocket.send_json(response)
    except Exception:
        pass


def run() -> None:
    """Run the API server."""
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
