"""Day 14 -- fix the e2e P&ID script filename + drawing title."""
from pathlib import Path

p = Path(r"C:\Users\TG\.mavis\workspace\nepal-decarb-build\demo-e2e\07_export_pid.py")
text = p.read_text(encoding="utf-8")
# Filename
text = text.replace("07_hetauda_cooler_pid.svg", "07_planta_cooler_pid.svg")
text = text.replace("07_hetauda_cooler_pid.json", "07_planta_cooler_pid.json")
# SVG title
text = text.replace(">Hetauda Cooler P&amp;ID<", ">PlantA Cooler P&amp;ID<")
# Drawing metadata: client + plant field
text = text.replace(
    '"Himalayan Carbon Nepal / Hetauda Cement Industries Ltd"',
    '"Generic cement plant (configurable per deployment)"',
)
text = text.replace('"plant":       "Hetauda",', '"plant":       "PlantA (generic — configure per deployment)",')
p.write_text(text, encoding="utf-8")
print("fixed e2e P&ID script")
