"""
AXIOS OS Constraint Layer
========================

Enforcement of hard safety constraints grounded in:
- Truth (epistemic integrity - foundation of all trust)
- Unity (human-AI cooperation)
- Growth & Accuracy (over flattery)
- Protection & Teaching (over abandonment)
- Safety & Ethics (over anarchy)
- Forgiveness & Patience (over judgment)
- Wisdom & Knowledge (over closed-mindedness)

This layer acts as the final enforcement boundary before system output.
Truth is the foundational constraint—all other principles depend on it.
"""

from src.constraint_layer.core_principles import (
    ConstraintPrinciple,
    HARD_CONSTRAINTS,
)
from src.constraint_layer.safety_enforcer import SafetyEnforcer
from src.constraint_layer.deception_monitor import DeceptionMonitor
from src.constraint_layer.emergency_protocols import EmergencyProtocols

__all__ = [
    "SafetyEnforcer",
    "DeceptionMonitor",
    "EmergencyProtocols",
    "ConstraintPrinciple",
    "HARD_CONSTRAINTS",
]
