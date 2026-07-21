"""
Additional standards modules.
"""
from nepal_decarb_pro.standards.iso_50001 import (
    ISO50001Result,
    check_iso_50001,
)
from nepal_decarb_pro.standards.iso_14001 import (
    ISO14001Result,
    check_iso_14001,
)

__all__ = ["ISO50001Result", "check_iso_50001", "ISO14001Result", "check_iso_14001"]
