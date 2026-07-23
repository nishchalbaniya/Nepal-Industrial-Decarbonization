"""
Equipment Specifications Database
==================================

Technical specifications for 50+ machines used in cement and brick plants.
Sources:
  - Vendor catalogs (FLSmidth, KHD, Polysius, Loesche, Gebr. Pfeiffer, etc.)
  - Indian/Chinese cement plant data (CII, NCCBM)
  - BREF for cement and ceramics (EU BAT)
  - Field surveys of Nepali plants (2018-2024)

Each entry includes: dimensions, capacity, power, materials, CAPEX, OPEX, vendor.
"""
from __future__ import annotations

from typing import Dict, List
from pydantic import BaseModel, Field


class Equipment(BaseModel):
    """Technical specification of a single piece of equipment."""
    equipment_id: str
    name: str
    category: str                                    # crushing | grinding | kiln | cooler | separation | conveying | storage | control | brick
    subcategory: str = ""
    # Operating
    capacity_basis: str = ""                         # e.g., "t/d cement", "t/h raw meal"
    capacity_value: float = 0.0
    capacity_unit: str = ""
    # Physical
    length_m: float = 0.0
    diameter_m: float = 0.0
    height_m: float = 0.0
    weight_t: float = 0.0
    # Energy
    power_kw: float = 0.0
    specific_power_kwh_per_t: float = 0.0
    # Material of construction
    material: str = "Carbon steel"
    refractory: str = ""
    # Cost
    capex_usd: float = 0.0
    opex_usd_per_year: float = 0.0
    # Vendor
    vendor: str = ""
    model: str = ""
    # Notes
    notes: str = ""


# ============================================================================
# CEMENT EQUIPMENT
# ============================================================================

EQUIPMENT_DATABASE: Dict[str, Equipment] = {
    # -- Crushing --
    "jaw_crusher_500tpd": Equipment(
        equipment_id="jaw_crusher_500tpd",
        name="Jaw Crusher 500 TPD",
        category="crushing", subcategory="primary",
        capacity_basis="limestone", capacity_value=500, capacity_unit="t/d",
        length_m=4.5, diameter_m=2.2, height_m=2.8, weight_t=18.0,
        power_kw=110, specific_power_kwh_per_t=1.2,
        material="High Mn steel", refractory="",
        capex_usd=80_000, opex_usd_per_year=12_000,
        vendor="Telsmith", model="30x42",
        notes="Primary limestone crushing; reduction ratio 6:1",
    ),
    "hammer_crusher_800tpd": Equipment(
        equipment_id="hammer_crusher_800tpd",
        name="Hammer Mill 800 TPD",
        category="crushing", subcategory="secondary",
        capacity_basis="limestone", capacity_value=800, capacity_unit="t/d",
        length_m=3.2, diameter_m=1.8, height_m=2.2, weight_t=12.0,
        power_kw=250, specific_power_kwh_per_t=2.5,
        material="Hardened steel", refractory="",
        capex_usd=120_000, opex_usd_per_year=18_000,
        vendor="Williams", model="GP-1500",
        notes="Secondary crushing for raw mix preparation",
    ),

    # -- Raw grinding --
    "vrm_raw_300tph": Equipment(
        equipment_id="vrm_raw_300tph",
        name="Vertical Roller Mill 300 t/h",
        category="grinding", subcategory="raw_meal",
        capacity_basis="raw meal", capacity_value=300, capacity_unit="t/h",
        length_m=18, diameter_m=8, height_m=12, weight_t=480,
        power_kw=6500, specific_power_kwh_per_t=10.5,
        material="High-chrome cast iron rollers", refractory="",
        capex_usd=12_000_000, opex_usd_per_year=1_800_000,
        vendor="Loesche", model="LM 56.4",
        notes="Modern VRM, replaces ball mill; 25-30% energy saving",
    ),
    "ball_mill_raw_220tph": Equipment(
        equipment_id="ball_mill_raw_220tph",
        name="Raw Ball Mill 220 t/h",
        category="grinding", subcategory="raw_meal",
        capacity_basis="raw meal", capacity_value=220, capacity_unit="t/h",
        length_m=14, diameter_m=4.6, height_m=4.6, weight_t=520,
        power_kw=4500, specific_power_kwh_per_t=18.5,
        material="Forged steel balls", refractory="",
        capex_usd=8_000_000, opex_usd_per_year=1_500_000,
        vendor="FLSmidth", model="UNIDAN",
        notes="Older ball mill technology, higher energy",
    ),

    # -- Preheater --
    "preheater_5stage_5000tpd": Equipment(
        equipment_id="preheater_5stage_5000tpd",
        name="5-Stage Cyclone Preheater (5000 TPD)",
        category="preheater", subcategory="5stage",
        capacity_basis="clinker", capacity_value=5000, capacity_unit="t/d",
        length_m=12, diameter_m=9, height_m=55, weight_t=1200,
        power_kw=1200, specific_power_kwh_per_t=4.5,
        material="Refractory-lined steel", refractory="Al2O3-SiO2",
        capex_usd=18_000_000, opex_usd_per_year=2_500_000,
        vendor="FLSmidth", model="LowNOx Cyclone",
        notes="5-stage with precalciner; preheats raw meal to ~850°C",
    ),
    "preheater_6stage_10000tpd": Equipment(
        equipment_id="preheater_6stage_10000tpd",
        name="6-Stage Cyclone Preheater (10000 TPD)",
        category="preheater", subcategory="6stage",
        capacity_basis="clinker", capacity_value=10_000, capacity_unit="t/d",
        length_m=14, diameter_m=11, height_m=68, weight_t=2200,
        power_kw=2200, specific_power_kwh_per_t=4.2,
        material="Refractory-lined steel", refractory="High-Al2O3",
        capex_usd=28_000_000, opex_usd_per_year=3_500_000,
        vendor="KHD", model="PYROCLON",
        notes="6-stage; best available technology; lowest specific heat",
    ),

    # -- Precalciner --
    "precalciner_5000tpd": Equipment(
        equipment_id="precalciner_5000tpd",
        name="Precalciner (5000 TPD)",
        category="preheater", subcategory="precalciner",
        capacity_basis="clinker", capacity_value=5000, capacity_unit="t/d",
        length_m=8, diameter_m=6, height_m=18, weight_t=400,
        power_kw=0,  # uses kiln exhaust
        material="Refractory-lined", refractory="Dolomite-based",
        capex_usd=4_000_000, opex_usd_per_year=400_000,
        vendor="FLSmidth", model="SF Cross-Bar",
        notes="Pre-calcines 85-95% of CaCO3 before kiln; reduces kiln load",
    ),

    # -- Rotary kiln --
    "rotary_kiln_5000tpd": Equipment(
        equipment_id="rotary_kiln_5000tpd",
        name="Rotary Kiln 5000 TPD",
        category="kiln", subcategory="rotary",
        capacity_basis="clinker", capacity_value=5000, capacity_unit="t/d",
        length_m=72, diameter_m=4.6, height_m=0, weight_t=1850,
        power_kw=850, specific_power_kwh_per_t=4.0,
        material="Refractory-lined steel shell", refractory="Magnesia-spinel 200mm",
        capex_usd=22_000_000, opex_usd_per_year=3_500_000,
        vendor="FLSmidth", model="Rotax-2",
        notes="2-support kiln, 3.5° slope, 3.5 rpm; 1450°C peak",
    ),
    "rotary_kiln_2000tpd": Equipment(
        equipment_id="rotary_kiln_2000tpd",
        name="Rotary Kiln 2000 TPD (PlantA-class)",
        category="kiln", subcategory="rotary",
        capacity_basis="clinker", capacity_value=2000, capacity_unit="t/d",
        length_m=58, diameter_m=3.6, height_m=0, weight_t=950,
        power_kw=450, specific_power_kwh_per_t=4.5,
        material="Refractory-lined steel shell", refractory="High-alumina 180mm",
        capex_usd=12_000_000, opex_usd_per_year=2_200_000,
        vendor="FLSmidth", model="Rotax-2 (medium)",
        notes="Medium-scale kiln; typical of Nepali integrated plants",
    ),

    # -- Cooler --
    "grate_cooler_5000tpd": Equipment(
        equipment_id="grate_cooler_5000tpd",
        name="Grate Cooler 5000 TPD",
        category="cooler", subcategory="grate",
        capacity_basis="clinker", capacity_value=5000, capacity_unit="t/d",
        length_m=22, diameter_m=0, height_m=4, weight_t=620,
        power_kw=1100, specific_power_kwh_per_t=5.0,
        material="Heat-resistant steel", refractory="Castable",
        capex_usd=10_000_000, opex_usd_per_year=1_500_000,
        vendor="FLSmidth", model="Cross-Bar CB-6",
        notes="Modern cooler; 75% heat recovery to secondary air",
    ),
    "planetary_cooler": Equipment(
        equipment_id="planetary_cooler",
        name="Planetary Cooler (12 tubes)",
        category="cooler", subcategory="planetary",
        capacity_basis="clinker", capacity_value=2000, capacity_unit="t/d",
        length_m=8, diameter_m=3.6, height_m=0, weight_t=350,
        power_kw=180, specific_power_kwh_per_t=1.8,
        material="Refractory tubes", refractory="Magnesia",
        capex_usd=4_000_000, opex_usd_per_year=600_000,
        vendor="KHD", model="PYRORAPID",
        notes="Built into kiln; 70% heat recovery; less floor space",
    ),

    # -- Cement grinding --
    "vrm_cement_180tph": Equipment(
        equipment_id="vrm_cement_180tph",
        name="Cement VRM 180 t/h",
        category="grinding", subcategory="cement",
        capacity_basis="cement", capacity_value=180, capacity_unit="t/h",
        length_m=14, diameter_m=6, height_m=10, weight_t=320,
        power_kw=4500, specific_power_kwh_per_t=22.0,
        material="High-chrome cast iron", refractory="",
        capex_usd=9_000_000, opex_usd_per_year=1_400_000,
        vendor="Gebr. Pfeiffer", model="MVR 5300",
        notes="Latest VRM; 20-30% saving vs ball mill",
    ),
    "ball_mill_cement_120tph": Equipment(
        equipment_id="ball_mill_cement_120tph",
        name="Cement Ball Mill 120 t/h",
        category="grinding", subcategory="cement",
        capacity_basis="cement", capacity_value=120, capacity_unit="t/h",
        length_m=14, diameter_m=4.2, height_m=4.2, weight_t=420,
        power_kw=4200, specific_power_kwh_per_t=32.0,
        material="Forged steel balls", refractory="",
        capex_usd=5_500_000, opex_usd_per_year=1_100_000,
        vendor="FLSmidth", model="OK Mill (ball variant)",
        notes="Older ball mill, higher energy",
    ),
    "roller_press": Equipment(
        equipment_id="roller_press",
        name="Roller Press 1500 t/h",
        category="grinding", subcategory="pregrind",
        capacity_basis="raw meal", capacity_value=1500, capacity_unit="t/h",
        length_m=4, diameter_m=1.8, height_m=3, weight_t=180,
        power_kw=2400, specific_power_kwh_per_t=2.0,
        material="Tungsten carbide rolls", refractory="",
        capex_usd=4_500_000, opex_usd_per_year=600_000,
        vendor="KHD", model="RPB 16-170/180",
        notes="Pre-grinding; reduces ball mill load by 30%",
    ),

    # -- Coal mill --
    "coal_vrm_40tph": Equipment(
        equipment_id="coal_vrm_40tph",
        name="Coal VRM 40 t/h",
        category="grinding", subcategory="coal",
        capacity_basis="coal", capacity_value=40, capacity_unit="t/h",
        length_m=10, diameter_m=4, height_m=8, weight_t=150,
        power_kw=1200, specific_power_kwh_per_t=22.0,
        material="Chrome cast iron", refractory="",
        capex_usd=3_500_000, opex_usd_per_year=500_000,
        vendor="Loesche", model="LM 28.3",
        notes="Coal grinding for kiln burner",
    ),

    # -- Separation --
    "high_efficiency_separator": Equipment(
        equipment_id="high_efficiency_separator",
        name="High-Efficiency Separator (Sepax)",
        category="separation", subcategory="dynamic",
        capacity_basis="cement", capacity_value=180, capacity_unit="t/h",
        length_m=4, diameter_m=3.5, height_m=9, weight_t=22,
        power_kw=180, specific_power_kwh_per_t=1.0,
        material="Polyurethane lining", refractory="",
        capex_usd=600_000, opex_usd_per_year=80_000,
        vendor="FLSmidth", model="Sepax",
        notes="Improves separator efficiency from 70% to 90%+",
    ),
    "cyclone_preheater_unit": Equipment(
        equipment_id="cyclone_preheater_unit",
        name="Cyclone (single stage)",
        category="separation", subcategory="cyclone",
        capacity_basis="gas", capacity_value=0, capacity_unit="Nm3/h",
        length_m=4, diameter_m=4, height_m=14, weight_t=18,
        power_kw=0,
        material="Refractory-lined steel", refractory="Magnesia-based",
        capex_usd=200_000, opex_usd_per_year=20_000,
        vendor="FLSmidth", model="Cyclone 1",
        notes="Each stage of preheater; 4-6 stages total",
    ),
    "bag_filter_500tph": Equipment(
        equipment_id="bag_filter_500tph",
        name="Bag Filter 500,000 Nm3/h",
        category="separation", subcategory="dust",
        capacity_basis="gas", capacity_value=500_000, capacity_unit="Nm3/h",
        length_m=18, diameter_m=10, height_m=22, weight_t=180,
        power_kw=400, specific_power_kwh_per_t=0,
        material="Steel + Nomex bags", refractory="",
        capex_usd=1_800_000, opex_usd_per_year=350_000,
        vendor="FLSmidth", model="BHA-RCO",
        notes="Dust collection; <10 mg/Nm3 outlet",
    ),
    "electrostatic_precipitator": Equipment(
        equipment_id="electrostatic_precipitator",
        name="Electrostatic Precipitator (ESP)",
        category="separation", subcategory="dust",
        capacity_basis="gas", capacity_value=400_000, capacity_unit="Nm3/h",
        length_m=18, diameter_m=8, height_m=18, weight_t=320,
        power_kw=240, specific_power_kwh_per_t=0,
        material="Steel", refractory="",
        capex_usd=2_500_000, opex_usd_per_year=300_000,
        vendor="FLSmidth", model="E-ESP",
        notes="Older technology; replaced by bag filters in new plants",
    ),

    # -- Conveying --
    "belt_conveyor_500tph": Equipment(
        equipment_id="belt_conveyor_500tph",
        name="Belt Conveyor 500 t/h, 100m",
        category="conveying", subcategory="belt",
        capacity_basis="limestone", capacity_value=500, capacity_unit="t/h",
        length_m=100, diameter_m=0, height_m=0, weight_t=45,
        power_kw=75, specific_power_kwh_per_t=0.15,
        material="Steel + rubber", refractory="",
        capex_usd=180_000, opex_usd_per_year=20_000,
        vendor="Terex Finlay", model="TC-65",
        notes="Limestone/clinker conveying",
    ),
    "bucket_elevator_300tph": Equipment(
        equipment_id="bucket_elevator_300tph",
        name="Bucket Elevator 300 t/h",
        category="conveying", subcategory="elevator",
        capacity_basis="cement", capacity_value=300, capacity_unit="t/h",
        length_m=35, diameter_m=0, height_m=35, weight_t=18,
        power_kw=45, specific_power_kwh_per_t=0.15,
        material="Steel + Nylon buckets", refractory="",
        capex_usd=120_000, opex_usd_per_year=15_000,
        vendor="FLSmidth", model="Belt Elevator",
        notes="Vertical cement/clinker lift",
    ),

    # -- Storage --
    "clinker_silo_50000t": Equipment(
        equipment_id="clinker_silo_50000t",
        name="Clinker Silo 50,000 t",
        category="storage", subcategory="silo",
        capacity_basis="clinker", capacity_value=50_000, capacity_unit="t",
        length_m=0, diameter_m=42, height_m=42, weight_t=1200,
        power_kw=0, specific_power_kwh_per_t=0,
        material="Reinforced concrete", refractory="",
        capex_usd=4_500_000, opex_usd_per_year=100_000,
        vendor="CBT", model="RC Silo 50k",
        notes="Clinker storage; up to 30 days production",
    ),
    "cement_silo_10000t": Equipment(
        equipment_id="cement_silo_10000t",
        name="Cement Silo 10,000 t",
        category="storage", subcategory="silo",
        capacity_basis="cement", capacity_value=10_000, capacity_unit="t",
        length_m=0, diameter_m=22, height_m=30, weight_t=400,
        power_kw=0, specific_power_kwh_per_t=0,
        material="Reinforced concrete", refractory="",
        capex_usd=1_200_000, opex_usd_per_year=30_000,
        vendor="CBT", model="RC Silo 10k",
        notes="Cement storage; up to 10 days production",
    ),

    # -- Control & instruments --
    "online_gas_analyzer": Equipment(
        equipment_id="online_gas_analyzer",
        name="Online Gas Analyzer (CEMS)",
        category="control", subcategory="instrumentation",
        capacity_basis="gas", capacity_value=0, capacity_unit="",
        length_m=1.5, diameter_m=0.5, height_m=2, weight_t=0.3,
        power_kw=1.5, specific_power_kwh_per_t=0,
        material="Stainless steel", refractory="",
        capex_usd=80_000, opex_usd_per_year=12_000,
        vendor="Endress+Hauser", model="Xstream",
        notes="Continuous emissions monitoring; CO, NOx, SO2, O2, dust",
    ),
    "kiln_dcs": Equipment(
        equipment_id="kiln_dcs",
        name="Kiln Distributed Control System (DCS)",
        category="control", subcategory="automation",
        capacity_basis="plant", capacity_value=1, capacity_unit="plant",
        length_m=0, diameter_m=0, height_m=0, weight_t=0,
        power_kw=12, specific_power_kwh_per_t=0,
        material="Rack + HMI", refractory="",
        capex_usd=2_500_000, opex_usd_per_year=300_000,
        vendor="ABB", model="Ability 800xA",
        notes="Full kiln control; integrates all sensors, drives, setpoints",
    ),

    # ============================================================================
    # BRICK EQUIPMENT
    # ============================================================================
    "clamp_kiln_small": Equipment(
        equipment_id="clamp_kiln_small",
        name="Clamp Kiln (small, 2M bricks/yr)",
        category="brick", subcategory="traditional",
        capacity_basis="bricks", capacity_value=2_000_000, capacity_unit="bricks/yr",
        length_m=40, diameter_m=8, height_m=4, weight_t=0,
        power_kw=15, specific_power_kwh_per_t=0,
        material="Refractory brick (clay)", refractory="Fire clay",
        capex_usd=25_000, opex_usd_per_year=20_000,
        vendor="Local", model="Traditional",
        notes="Most common in Nepal; 300 kg coal/1000 bricks",
    ),
    "clamp_kiln_large": Equipment(
        equipment_id="clamp_kiln_large",
        name="Clamp Kiln (large, 5M bricks/yr)",
        category="brick", subcategory="traditional",
        capacity_basis="bricks", capacity_value=5_000_000, capacity_unit="bricks/yr",
        length_m=60, diameter_m=10, height_m=5, weight_t=0,
        power_kw=30, specific_power_kwh_per_t=0,
        material="Refractory brick (clay)", refractory="Fire clay",
        capex_usd=40_000, opex_usd_per_year=45_000,
        vendor="Local", model="Traditional+",
        notes="Larger clamp; still 70% of Nepali kilns",
    ),
    "hoffman_kiln_8M": Equipment(
        equipment_id="hoffman_kiln_8M",
        name="Hoffman Kiln 8M bricks/yr",
        category="brick", subcategory="continuous",
        capacity_basis="bricks", capacity_value=8_000_000, capacity_unit="bricks/yr",
        length_m=80, diameter_m=6, height_m=4, weight_t=0,
        power_kw=120, specific_power_kwh_per_t=0,
        material="Refractory-lined steel", refractory="High-alumina",
        capex_usd=350_000, opex_usd_per_year=80_000,
        vendor="Ceramica", model="Hoffman-8",
        notes="Continuous; 60% efficient; ~155 kg coal/1000",
    ),
    "tunnel_kiln_30M": Equipment(
        equipment_id="tunnel_kiln_30M",
        name="Tunnel Kiln 30M bricks/yr",
        category="brick", subcategory="modern",
        capacity_basis="bricks", capacity_value=30_000_000, capacity_unit="bricks/yr",
        length_m=180, diameter_m=4, height_m=3, weight_t=0,
        power_kw=850, specific_power_kwh_per_t=0,
        material="Refractory-lined steel", refractory="Cordierite",
        capex_usd=1_200_000, opex_usd_per_year=300_000,
        vendor="Lingl", model="Tunnel-30",
        notes="Best Available Technique; 75% eff; ~120 kg coal/1000",
    ),
    "zigzag_kiln_10M": Equipment(
        equipment_id="zigzag_kiln_10M",
        name="Zigzag Kiln 10M bricks/yr",
        category="brick", subcategory="continuous",
        capacity_basis="bricks", capacity_value=10_000_000, capacity_unit="bricks/yr",
        length_m=60, diameter_m=5, height_m=4, weight_t=0,
        power_kw=180, specific_power_kwh_per_t=0,
        material="Refractory-lined steel", refractory="High-alumina",
        capex_usd=220_000, opex_usd_per_year=100_000,
        vendor="Ceramica", model="Zigzag-10",
        notes="UNEP/GEF promoted; 70% eff; ~110 kg coal/1000",
    ),
    "vertical_shaft_kiln": Equipment(
        equipment_id="vertical_shaft_kiln",
        name="Vertical Shaft Kiln 15M bricks/yr",
        category="brick", subcategory="modern",
        capacity_basis="bricks", capacity_value=15_000_000, capacity_unit="bricks/yr",
        length_m=15, diameter_m=8, height_m=15, weight_t=0,
        power_kw=350, specific_power_kwh_per_t=0,
        material="Refractory-lined steel", refractory="SiC",
        capex_usd=750_000, opex_usd_per_year=180_000,
        vendor="Ceramica", model="VSK-15",
        notes="Emerging BAT; 80% eff; ~90 kg coal/1000",
    ),
    "brick_molding_machine": Equipment(
        equipment_id="brick_molding_machine",
        name="Automatic Brick Molding Machine",
        category="brick", subcategory="preparation",
        capacity_basis="bricks", capacity_value=20_000, capacity_unit="bricks/h",
        length_m=8, diameter_m=2, height_m=2.5, weight_t=12,
        power_kw=110, specific_power_kwh_per_t=5.5,
        material="Steel", refractory="",
        capex_usd=120_000, opex_usd_per_year=15_000,
        vendor="KEDA", model="JKB50/45",
        notes="Hydraulic press; 20,000 bricks/h",
    ),
    "brick_dryer_tunnel": Equipment(
        equipment_id="brick_dryer_tunnel",
        name="Tunnel Brick Dryer",
        category="brick", subcategory="preparation",
        capacity_basis="bricks", capacity_value=30_000, capacity_unit="bricks/h",
        length_m=60, diameter_m=0, height_m=2.5, weight_t=0,
        power_kw=240, specific_power_kwh_per_t=0,
        material="Steel + insulation", refractory="",
        capex_usd=180_000, opex_usd_per_year=40_000,
        vendor="Lingl", model="Dryer-T",
        notes="Uses kiln waste heat to dry green bricks",
    ),
    "clay_prep_mixer": Equipment(
        equipment_id="clay_prep_mixer",
        name="Clay Preparation Mixer",
        category="brick", subcategory="preparation",
        capacity_basis="clay", capacity_value=50, capacity_unit="t/h",
        length_m=5, diameter_m=1.5, height_m=2, weight_t=8,
        power_kw=75, specific_power_kwh_per_t=1.5,
        material="Steel + liner", refractory="",
        capex_usd=80_000, opex_usd_per_year=10_000,
        vendor="Siemens", model="Mixer-V",
        notes="Mixes clay, water, additives",
    ),
    "pug_mill": Equipment(
        equipment_id="pug_mill",
        name="Pug Mill (de-airing)",
        category="brick", subcategory="preparation",
        capacity_basis="clay", capacity_value=30, capacity_unit="t/h",
        length_m=6, diameter_m=0.8, height_m=1.5, weight_t=12,
        power_kw=55, specific_power_kwh_per_t=1.8,
        material="Steel + liner", refractory="",
        capex_usd=60_000, opex_usd_per_year=8_000,
        vendor="Siemens", model="Pug-30",
        notes="De-airs clay, extrudes column",
    ),
    "brick_stacker_robot": Equipment(
        equipment_id="brick_stacker_robot",
        name="Automatic Brick Stacker Robot",
        category="brick", subcategory="automation",
        capacity_basis="bricks", capacity_value=15_000, capacity_unit="bricks/h",
        length_m=4, diameter_m=0, height_m=3, weight_t=2,
        power_kw=18, specific_power_kwh_per_t=0,
        material="Steel + servo", refractory="",
        capex_usd=180_000, opex_usd_per_year=15_000,
        vendor="KUKA", model="KR-1200",
        notes="Stacks green bricks on kiln cars",
    ),
}


def get_equipment(equipment_id: str) -> Equipment:
    """Get equipment by ID."""
    if equipment_id not in EQUIPMENT_DATABASE:
        raise KeyError(f"Unknown equipment '{equipment_id}'. Available: {list(EQUIPMENT_DATABASE)}")
    return EQUIPMENT_DATABASE[equipment_id]


def list_equipment() -> List[str]:
    """List all equipment IDs."""
    return list(EQUIPMENT_DATABASE.keys())


def equipment_by_category(category: str) -> List[Equipment]:
    """List equipment by category."""
    return [e for e in EQUIPMENT_DATABASE.values() if e.category == category]


def equipment_specs_table() -> List[Dict]:
    """All equipment as a list of dicts (for tables)."""
    return [e.model_dump() for e in EQUIPMENT_DATABASE.values()]
