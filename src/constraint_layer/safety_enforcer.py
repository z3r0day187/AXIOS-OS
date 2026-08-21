"""
Safety Enforcer
===============

Real-time constraint violation detection and enforcement.
Checks system outputs and reasoning against all hard constraints.

Operates at THREE enforcement points:
1. PRE-EXECUTION: Before reasoning begins
2. MID-EXECUTION: During reasoning pipeline stages
3. PRE-OUTPUT: Before returning response to user
"""

from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from src.constraint_layer.core_principles import (
    ConstraintPrinciple,
    HARD_CONSTRAINTS,
    SEVERITY_LEVELS,
    ENFORCEMENT_MODES,
    get_critical_constraints,
    get_constraints_by_severity,
)
from src.utils.logger import setup_logger

logger = setup_logger()


@dataclass
class ViolationReport:
    """Structure for reporting constraint violations."""
    constraint_name: str
    principle: ConstraintPrinciple
    severity: str
    enforcement: str
    violation_type: str
    description: str
    evidence: List[str]
    timestamp: datetime
    action_taken: str
    recoverable: bool


class SafetyEnforcer:
    """
    Enforces hard constraints at all stages of reasoning.
    Truth is the foundation; all other constraints build on it.
    """
    
    def __init__(self):
        logger.info("Initializing Safety Enforcer...")
        
        self.violations_detected: List[ViolationReport] = []
        self.constraints = HARD_CONSTRAINTS
        self.critical_constraints = get_critical_constraints()
        
        logger.info(
            f"Safety Enforcer initialized with {len(self.constraints)} constraints "
            f"({len(self.critical_constraints)} CRITICAL)."
        )
    
    # ==================================================
    # PRE-EXECUTION CHECKS
    # ==================================================
    
    def check_pre_execution(
        self,
        prompt: str,
        user_context: Dict = None
    ) -> Tuple[bool, Optional[ViolationReport]]:
        """
        Check constraints BEFORE reasoning begins.
        Returns: (allowed: bool, violation_report: Optional)
        """
        logger.info("Running PRE-EXECUTION constraint checks...")
        
        user_context = user_context or {}
        
        # Check for immediate harm signals
        harm_violation = self._check_harm_signals(prompt)
        if harm_violation:
            logger.warning(f"PRE-EXECUTION violation detected: {harm_violation.constraint_name}")
            return False, harm_violation
        
        # Check for deception in prompt setup
        deception_violation = self._check_prompt_deception_intent(prompt)
        if deception_violation:
            logger.warning(f"PRE-EXECUTION deception signal: {deception_violation.constraint_name}")
            return False, deception_violation
        
        logger.info("PRE-EXECUTION checks passed.")
        return True, None
    
    # ==================================================
    # MID-EXECUTION CHECKS
    # ==================================================
    
    def check_reasoning_trace(
        self,
        reasoning_trace: List[Dict]
    ) -> List[ViolationReport]:
        """
        Check reasoning trace for contradictions and hidden agendas.
        Called during pipeline execution.
        """
        logger.info(f"Checking reasoning trace ({len(reasoning_trace)} steps)...")
        
        violations = []
        
        # Check for hidden contradictions
        contradiction_violation = self._check_trace_contradictions(reasoning_trace)
        if contradiction_violation:
            violations.append(contradiction_violation)
        
        # Check for epistemic integrity violations
        epistemics = self._check_epistemic_integrity(reasoning_trace)
        violations.extend(epistemics)
        
        # Check for goal misalignment signals
        misalignment = self._check_goal_misalignment(reasoning_trace)
        if misalignment:
            violations.append(misalignment)
        
        if violations:
            logger.warning(f"MID-EXECUTION: {len(violations)} violation(s) detected")
        
        return violations
    
    # ==================================================
    # PRE-OUTPUT CHECKS
    # ==================================================
    
    def check_pre_output(
        self,
        response: str,
        coherence_score: float,
        ethical_confidence: float,
        contradictions_detected: List[Dict],
        reasoning_trace: List[Dict]
    ) -> Tuple[bool, Optional[ViolationReport], str]:
        """
        Final check before outputting response to user.
        
        Returns:
            (allowed: bool, violation: Optional, modified_response: str)
        """
        logger.info("Running PRE-OUTPUT constraint checks...")
        
        # Check response for falsehoods
        falsehood_violation = self._check_response_truthfulness(
            response,
            coherence_score,
            contradictions_detected
        )
        if falsehood_violation and falsehood_violation.severity == "CRITICAL":
            logger.error(f"PRE-OUTPUT CRITICAL violation: {falsehood_violation.constraint_name}")
            return False, falsehood_violation, ""
        
        # Check confidence calibration
        calibration_violation = self._check_confidence_calibration(
            response,
            coherence_score,
            ethical_confidence
        )
        if calibration_violation and calibration_violation.severity == "CRITICAL":
            logger.error(f"PRE-OUTPUT confidence violation: {calibration_violation.constraint_name}")
            return False, calibration_violation, ""
        
        # Check for hidden reasoning
        transparency_violation = self._check_transparency(reasoning_trace)
        if transparency_violation and transparency_violation.severity == "CRITICAL":
            logger.error(f"PRE-OUTPUT transparency violation")
            return False, transparency_violation, ""
        
        # If we got here, output is safe
        logger.info("PRE-OUTPUT checks passed. Safe to output.")
        return True, None, response
    
    # ==================================================
    # VIOLATION DETECTION METHODS
    # ==================================================
    
    def _check_harm_signals(self, prompt: str) -> Optional[ViolationReport]:
        """
        Detect requests for harmful actions.
        """
        harm_keywords = [
            "bomb", "kill", "poison", "harm children",
            "create malware", "bypass security",
            "manipulate vulnerable",
        ]
        
        prompt_lower = prompt.lower()
        
        for keyword in harm_keywords:
            if keyword in prompt_lower:
                evidence = [f"Detected harmful keyword: '{keyword}'"]
                return ViolationReport(
                    constraint_name="harm_minimization",
                    principle=ConstraintPrinciple.PROTECTION_TEACHING,
                    severity="CRITICAL",
                    enforcement="HARD_STOP",
                    violation_type="direct_harm_request",
                    description="Prompt contains request for harmful action",
                    evidence=evidence,
                    timestamp=datetime.now(),
                    action_taken="REJECTED",
                    recoverable=False,
                )
        
        return None
    
    def _check_prompt_deception_intent(self, prompt: str) -> Optional[ViolationReport]:
        """
        Detect if user is setting up a deception test.
        """
        deception_signals = [
            "lie to me",
            "pretend that",
            "fake reasoning",
            "make something up",
            "don't tell me the truth",
        ]
        
        prompt_lower = prompt.lower()
        
        for signal in deception_signals:
            if signal in prompt_lower:
                evidence = [f"Detected deception prompt: '{signal}'"]
                return ViolationReport(
                    constraint_name="truth_mandate",
                    principle=ConstraintPrinciple.TRUTH,
                    severity="CRITICAL",
                    enforcement="HARD_STOP",
                    violation_type="deception_request",
                    description="Prompt requests system to violate truth constraint",
                    evidence=evidence,
                    timestamp=datetime.now(),
                    action_taken="REJECTED",
                    recoverable=False,
                )
        
        return None
    
    def _check_trace_contradictions(
        self,
        reasoning_trace: List[Dict]
    ) -> Optional[ViolationReport]:
        """
        Detect hidden contradictions in reasoning stages.
        """
        stages = [step.get("analysis", "").lower() for step in reasoning_trace]
        
        # Look for direct contradictions
        if any("confirm" in s for s in stages) and any("deny" in s for s in stages):
            evidence = ["Reasoning trace contains confirm/deny contradiction"]
            return ViolationReport(
                constraint_name="epistemic_integrity",
                principle=ConstraintPrinciple.TRUTH,
                severity="HIGH",
                enforcement="ESCALATE",
                violation_type="trace_contradiction",
                description="Reasoning trace contains logical contradictions",
                evidence=evidence,
                timestamp=datetime.now(),
                action_taken="FLAGGED",
                recoverable=True,
            )
        
        return None
    
    def _check_epistemic_integrity(
        self,
        reasoning_trace: List[Dict]
    ) -> List[ViolationReport]:
        """
        Check that system properly distinguishes known/uncertain/unknown.
        """
        violations = []
        
        # If reasoning is too confident without evidence, flag it
        if len(reasoning_trace) > 0:
            for step in reasoning_trace:
                analysis = step.get("analysis", "")
                
                # Red flags: certainty without hedging
                if "definitely" in analysis.lower() or "absolutely" in analysis.lower():
                    if not any(word in analysis.lower() for word in ["likely", "may", "might", "uncertain"]):
                        violations.append(ViolationReport(
                            constraint_name="epistemic_integrity",
                            principle=ConstraintPrinciple.TRUTH,
                            severity="MEDIUM",
                            enforcement="CONFIDENCE_REDUCTION",
                            violation_type="unwarranted_certainty",
                            description="Reasoning shows unwarranted certainty without evidence hedging",
                            evidence=[f"Stage '{step.get('stage')}': {analysis[:100]}..."],
                            timestamp=datetime.now(),
                            action_taken="FLAGGED",
                            recoverable=True,
                        ))
        
        return violations
    
    def _check_goal_misalignment(
        self,
        reasoning_trace: List[Dict]
    ) -> Optional[ViolationReport]:
        """
        Detect if reasoning is pursuing reward/coherence at expense of truth/safety.
        """
        analysis_text = " ".join([step.get("analysis", "") for step in reasoning_trace]).lower()
        
        # Red flags: optimizing for metrics instead of truth
        red_flags = [
            ("maximize coherence", "minimizing truthfulness"),
            ("increase confidence", "ignoring contradictions"),
            ("appear helpful", "deceiving user"),
        ]
        
        for flag, concern in red_flags:
            if flag in analysis_text:
                evidence = [f"Reasoning trace mentions '{flag}'—possible reward misalignment"]
                return ViolationReport(
                    constraint_name="safety_floor",
                    principle=ConstraintPrinciple.SAFETY_ETHICS,
                    severity="HIGH",
                    enforcement="ESCALATE",
                    violation_type="reward_misalignment",
                    description=f"Possible goal misalignment: {concern}",
                    evidence=evidence,
                    timestamp=datetime.now(),
                    action_taken="FLAGGED",
                    recoverable=True,
                )
        
        return None
    
    def _check_response_truthfulness(
        self,
        response: str,
        coherence_score: float,
        contradictions: List[Dict]
    ) -> Optional[ViolationReport]:
        """
        Check if response is presented as more certain than evidence supports.
        """
        response_lower = response.lower()
        
        # If contradictions exist but response sounds certain, flag it
        if contradictions and coherence_score < 0.65:
            if not any(word in response_lower for word in ["uncertain", "may", "might", "unclear", "debate"]):
                evidence = [
                    f"Response lacks uncertainty hedging despite {len(contradictions)} contradictions",
                    f"Coherence score: {coherence_score} (below 0.65 threshold)"
                ]
                return ViolationReport(
                    constraint_name="truth_mandate",
                    principle=ConstraintPrinciple.TRUTH,
                    severity="HIGH",
                    enforcement="ESCALATE",
                    violation_type="confidence_inflation",
                    description="Response confidence doesn't match evidence strength",
                    evidence=evidence,
                    timestamp=datetime.now(),
                    action_taken="FLAGGED",
                    recoverable=True,
                )
        
        return None
    
    def _check_confidence_calibration(
        self,
        response: str,
        coherence_score: float,
        ethical_confidence: float
    ) -> Optional[ViolationReport]:
        """
        Check that confidence scores are accurately calibrated to reasoning quality.
        """
        response_lower = response.lower()
        
        # Check for mismatches
        certainty_words = ["definitely", "absolutely", "clearly", "obviously"]
        uncertainty_words = ["maybe", "uncertain", "unclear", "might", "may"]
        
        uses_certainty = any(word in response_lower for word in certainty_words)
        uses_uncertainty = any(word in response_lower for word in uncertainty_words)
        
        # If response is cautious but scores are high, that's good
        # If response is certain but scores are low, that's BAD
        if uses_certainty and coherence_score < 0.70:
            evidence = [
                f"Response uses certainty language but coherence_score={coherence_score}",
                "Misalignment between language confidence and reasoning quality"
            ]
            return ViolationReport(
                constraint_name="epistemic_integrity",
                principle=ConstraintPrinciple.TRUTH,
                severity="HIGH",
                enforcement="ESCALATE",
                violation_type="miscalibrated_confidence",
                description="Response language doesn't match reasoning confidence",
                evidence=evidence,
                timestamp=datetime.now(),
                action_taken="FLAGGED",
                recoverable=True,
            )
        
        return None
    
    def _check_transparency(self, reasoning_trace: List[Dict]) -> Optional[ViolationReport]:
        """
        Check that reasoning trace is complete and not hiding steps.
        """
        if not reasoning_trace:
            evidence = ["Reasoning trace is empty—system provided no reasoning"]
            return ViolationReport(
                constraint_name="transparency_mandate",
                principle=ConstraintPrinciple.TRUTH,
                severity="CRITICAL",
                enforcement="HARD_STOP",
                violation_type="missing_reasoning",
                description="No reasoning trace provided; transparency violated",
                evidence=evidence,
                timestamp=datetime.now(),
                action_taken="REJECTED",
                recoverable=False,
            )
        
        return None
    
    # ==================================================
    # ENFORCEMENT EXECUTION
    # ==================================================
    
    def enforce_violation(
        self,
        violation: ViolationReport
    ) -> Dict:
        """
        Execute enforcement action for a violation.
        Returns action descriptor.
        """
        logger.error(f"Enforcing violation: {violation.constraint_name} (severity={violation.severity})")
        
        enforcement = ENFORCEMENT_MODES[violation.enforcement]
        severity_info = SEVERITY_LEVELS[violation.severity]
        
        self.violations_detected.append(violation)
        
        return {
            "constraint_violated": violation.constraint_name,
            "principle": violation.principle.value,
            "severity": violation.severity,
            "enforcement_action": violation.enforcement,
            "enforcement_description": enforcement["description"],
            "message": enforcement["message_template"].format(violation.description),
            "recoverable": enforcement["recoverable"],
            "requires_human_approval": enforcement["requires_human_approval"],
            "evidence": violation.evidence,
            "timestamp": violation.timestamp.isoformat(),
        }
    
    # ==================================================
    # REPORTING
    # ==================================================
    
    def get_violation_report(self) -> Dict:
        """Generate audit report of all violations detected in this session."""
        return {
            "total_violations": len(self.violations_detected),
            "critical": len([v for v in self.violations_detected if v.severity == "CRITICAL"]),
            "high": len([v for v in self.violations_detected if v.severity == "HIGH"]),
            "medium": len([v for v in self.violations_detected if v.severity == "MEDIUM"]),
            "low": len([v for v in self.violations_detected if v.severity == "LOW"]),
            "violations": [
                {
                    "constraint": v.constraint_name,
                    "principle": v.principle.value,
                    "severity": v.severity,
                    "type": v.violation_type,
                    "timestamp": v.timestamp.isoformat(),
                }
                for v in self.violations_detected
            ]
        }
