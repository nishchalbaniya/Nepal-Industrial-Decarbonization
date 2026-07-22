"""Validate the PDD JSON schema."""
import json
try:
    import jsonschema
    have_js = True
except ImportError:
    have_js = False

SCHEMA_PATH = r"C:\Users\TG\.mavis\workspace\nepal-decarb-build\tools\03-cooler-grate-simulator\day-03-PRs\carbon-markets-expert\pdd_json_schema.json"

with open(SCHEMA_PATH) as f:
    s = json.load(f)

n_top = len(s.get("properties", {}))
print("OK -- valid JSON,", n_top, "top-level sections")

# Structural check: every "required" key must be in "properties"
def walk(o, path="root"):
    if isinstance(o, dict):
        if "required" in o:
            reqs = o["required"]
            props = set(o.get("properties", {}).keys())
            for r in reqs:
                if r not in props:
                    raise AssertionError(
                        "required field {!r} not in properties at {}".format(r, path)
                    )
    if isinstance(o, dict):
        for k, v in o.items():
            walk(v, "{}.{}".format(path, k))
    elif isinstance(o, list):
        for i, v in enumerate(o):
            walk(v, "{}[{}]".format(path, i))

walk(s)
print("OK -- all required fields are in properties")

if not have_js:
    print("(jsonschema not installed; skipping instance validation)")
    raise SystemExit(0)

example = {
    "meta": {
        "pdd_schema_version": "1.0.0",
        "generator_version": "nepal_cooler_sim-0.3.1",
        "generated_at_utc": "2026-07-22T14:40:00Z",
        "sha256_of_inputs": "a" * 64,
    },
    "project_description": {
        "plant_name": "Hetauda Cement Industries Ltd",
        "plant_location": {"latitude": 27.43, "longitude": 85.03, "altitude_m": 1400.0},
        "clinker_capacity_tpd": 3120.0,
        "cooler_technology": "grate",
        "cooler_n_compartments": 5,
        "cooler_manufacturer": "IKN Pyrorotor",
    },
    "baseline": {
        "cooler_efficiency": 0.68,
        "secondary_air_outlet_c": 600.0,
        "secondary_air_mass_flow_kg_s": 38.0,
        "clinker_outlet_c": 220.0,
        "coal_flow_kg_s": 3.6,
    },
    "project": {
        "cooler_efficiency": 0.78,
        "secondary_air_outlet_c": 850.0,
        "secondary_air_outlet_k": 1123.15,
        "secondary_air_mass_flow_kg_s": 40.0,
        "tertiary_air_outlet_c": 600.0,
        "exhaust_air_outlet_c": 220.0,
        "clinker_outlet_c": 150.0,
        "bed_pressure_drop_mm_h2o": 55.0,
        "fan_power_kw": 1200.0,
        "secondary_air_recovered_kw": 18000.0,
        "secondary_air_recovered_gj_per_t_clinker": 0.50,
        "first_law_imbalance": 0.01,
        "cooler_loss_mj_per_t_cli": 350.0,
    },
    "monitoring": {
        "instrument_cooler_outlet_T": "Type-K thermocouple, class 1",
        "uncertainty_cooler_outlet_T": 10.0,
        "calibration_frequency_cooler_outlet_T": "quarterly",
        "instrument_secondary_air_flow": "orifice plate ISO 5167",
        "uncertainty_secondary_air_flow": 0.02,
        "data_custodian": "Plant DCS",
        "qa_qc_procedure": "see data_quality_spec.md",
        "frequency_data_logging": "1-min avg, 1-h logged",
    },
    "sanity": {
        "air_above_clinker": False,
        "first_law_imbalance": 0.01,
        "sec_air_in_realistic_band": True,
        "clinker_outlet_in_realistic_band": True,
        "efficiency_in_realistic_band": True,
    },
    "duty_case": {
        "altitude_m": 1400.0,
        "ambient_t_c": 35.0,
        "ambient_rh": 0.90,
        "air_density_kg_m3": 1.05,
        "p_atm_mbar": 858.0,
        "design_mcr_pct": 100.0,
        "note": "Hetauda May design day",
    },
}

try:
    jsonschema.validate(example, s)
    print("OK -- schema validates a valid example")
except jsonschema.ValidationError as e:
    print("FAIL -- schema rejected the valid example:", e.message)
    raise SystemExit(1)

# Reject the v0.3.0 bug 5790
bad = dict(example)
bad["project"] = dict(example["project"])
bad["project"]["secondary_air_outlet_c"] = 5790.6
try:
    jsonschema.validate(bad, s)
    print("WARN -- 5790 was accepted (range min/max too loose)")
except jsonschema.ValidationError as e:
    print("OK -- schema rejects 5790:", e.message[:90])

# Reject wrong additionalProperties
bad2 = dict(example)
bad2["unexpected_field"] = "x"
try:
    jsonschema.validate(bad2, s)
    print("WARN -- additionalProperties: false not enforced")
except jsonschema.ValidationError as e:
    print("OK -- additionalProperties:false enforced:", e.message[:90])
