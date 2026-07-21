"""Internationalization: English + Nepali (नेपाली) translations."""
from typing import Dict

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "Nepal Industrial Decarbonization Platform",
        "app_subtitle": "Cement & Brick Decarbonization Suite",
        "tab_dashboard": "Dashboard",
        "tab_cement": "Cement Baseline",
        "tab_brick": "Brick Baseline",
        "tab_optimize": "Fuel Optimization",
        "tab_uncertainty": "Uncertainty",
        "tab_lca": "LCA",
        "tab_pinch": "Pinch",
        "tab_market": "Carbon Markets",
        "tab_standards": "Standards",
        "tab_forecast": "Forecast",
        "button_calculate": "Calculate",
        "button_export": "Export PDF",
        "metric_total_emissions": "Total Emissions",
        "metric_intensity": "Intensity",
        "metric_reduction": "Reduction",
        "metric_npv": "NPV Revenue",
        "label_year": "Reporting Year",
        "label_location": "Location",
        "label_clinker_t": "Clinker Production (t/yr)",
        "label_cement_t": "Cement Production (t/yr)",
        "label_bricks": "Annual Brick Production",
        "label_kiln": "Kiln Type",
        "label_coal_t": "Coal (t/yr)",
        "label_petcoke_t": "Petcoke (t/yr)",
        "label_biomass_t": "Biomass (t/yr)",
        "label_elec_kwh": "Electricity (kWh/yr)",
    },
    "ne": {
        "app_title": "नेपाल औद्योगिक डिकार्बोनाइजेसन प्लेटफर्म",
        "app_subtitle": "सिमेन्ट र इँटा डिकार्बोनाइजेसन सुइट",
        "tab_dashboard": "ड्यासबोर्ड",
        "tab_cement": "सिमेन्ट आधाररेखा",
        "tab_brick": "इँटा आधाररेखा",
        "tab_optimize": "इन्धन अनुकूलन",
        "tab_uncertainty": "अनिश्चितता",
        "tab_lca": "जीवनचक्र मूल्यांकन",
        "tab_pinch": "पिन्च",
        "tab_market": "कार्बन बजार",
        "tab_standards": "मापदण्डहरू",
        "tab_forecast": "पूर्वानुमान",
        "button_calculate": "गणना गर्नुहोस्",
        "button_export": "PDF निर्यात गर्नुहोस्",
        "metric_total_emissions": "कुल उत्सर्जन",
        "metric_intensity": "तीव्रता",
        "metric_reduction": "कमी",
        "metric_npv": "NPV आम्दानी",
        "label_year": "प्रतिवेदन वर्ष",
        "label_location": "स्थान",
        "label_clinker_t": "क्लिंकर उत्पादन (ट/वर्ष)",
        "label_cement_t": "सिमेन्ट उत्पादन (ट/वर्ष)",
        "label_bricks": "वार्षिक इँटा उत्पादन",
        "label_kiln": "भट्टी प्रकार",
        "label_coal_t": "कोइला (ट/वर्ष)",
        "label_petcoke_t": "पेटकोक (ट/वर्ष)",
        "label_biomass_t": "जैविक इन्धन (ट/वर्ष)",
        "label_elec_kwh": "विद्युत (किलोवाट-घण्टा/वर्ष)",
    },
}


def t(key: str, lang: str = "en") -> str:
    """Translate a key."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(
        key, TRANSLATIONS["en"].get(key, key)
    )
