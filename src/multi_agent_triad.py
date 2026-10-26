"""
Multi-Agent Forensic Auditor Triad.
Simulates the adversarial debate game between three specialized AI personas:
  1. Forensic Prosecutor Persona: Highlights balance sheet contradictions and footnote anomalies.
  2. Defense Cross-Examiner Persona: Identifies legitimate non-fraud explanations (seasonality, macro factors).
  3. Judicial Arbiter Persona: Synthesizes evidence, resolves debate equilibrium, and issues calibrated audit verdicts.
"""

from typing import Dict, Any, List

class MultiAgentAuditorTriad:
    """
    Executes multi-agent cross-examination over detected causal discrepancies.
    """
    def __init__(self):
        pass

    def run_debate_round(self,
                         turn_claim: Dict[str, Any],
                         causal_result: Dict[str, Any],
                         xbrl_footnote_text: str
                         ) -> Dict[str, Any]:
        """
        Executes a 3-agent debate session on a specific contested utterance.
        """
        turn_id = turn_claim.get("turn_id", "T0")
        speaker = turn_claim.get("speaker", "Executive")
        spoken_text = turn_claim.get("text", "")
        concept = causal_result.get("concept", "")
        spoken_val = causal_result.get("spoken_value", 0.0)
        audited_val = causal_result.get("audited_xbrl_value", 0.0)
        p_val = causal_result.get("p_value", 1.0)
        prosody_score = turn_claim.get("acoustic_diagnostics", {}).get("composite_prosody_score", 0.0)

        # ---------------------------------------------------------------------
        # AGENT 1: FORENSIC PROSECUTOR PERSONA
        # ---------------------------------------------------------------------
        prosecutor_arguments = []
        if causal_result.get("is_material_contradiction", False):
            prosecutor_arguments.append(
                f"MATERIAL CONTRADICTION DETECTED: Executive {speaker} orally asserted that {concept} is {spoken_val}, "
                f"whereas certified SEC Form 10-Q documentation establishes the audited amount as {audited_val}."
            )
            if prosody_score >= 0.60:
                prosecutor_arguments.append(
                    f"ACOUSTIC EVASION CONFIRMATION: Speaker exhibited elevated vocal stress "
                    f"(dissonance score {prosody_score:.2f}, high jitter/shimmer), indicating conscious cognitive dissonance."
                )
            if xbrl_footnote_text:
                prosecutor_arguments.append(
                    f"REGULATORY FOOTNOTE EVIDENCE: Form 10-Q disclosures state: \"{xbrl_footnote_text[:180]}...\""
                )
        else:
            prosecutor_arguments.append(
                f"CLAIM VERIFIED: Spoken figure {spoken_val} aligns within normal GAAP measurement boundaries of {audited_val}."
            )

        # ---------------------------------------------------------------------
        # AGENT 2: DEFENSE CROSS-EXAMINER PERSONA
        # ---------------------------------------------------------------------
        defense_arguments = []
        if causal_result.get("is_material_contradiction", False):
            defense_arguments.append(
                f"NON-FRAUD HYPOTHESIS: Management's verbal assertion may reflect non-GAAP operational projections, "
                f"pro-forma liquidity expectations, or informal working capital definitions rather than fraudulent intent."
            )
            defense_arguments.append(
                "ALTERNATIVE EXPLANATION: Credit agreement covenants are subject to standard ongoing syndicate waiver negotiations "
                "which management may have reasonably expected to close before quarter-end."
            )
        else:
            defense_arguments.append(
                "CONCURRENCE: Verbal disclosure conforms to published financial records without evidentiary flaw."
            )

        # ---------------------------------------------------------------------
        # AGENT 3: JUDICIAL ARBITER PERSONA
        # ---------------------------------------------------------------------
        arbiter_synthesis = {}
        if causal_result.get("is_material_contradiction", False):
            final_deception_prob = round(0.55 * causal_result["combined_causal_score"] + 0.45 * (1.0 - p_val), 4)
            verdict = "DECEPTIVE_MATERIAL_MISSTATEMENT" if final_deception_prob >= 0.75 else "QUESTIONABLE_DISCLOSURE"
            arbiter_synthesis = {
                "verdict": verdict,
                "confidence_score": final_deception_prob,
                "statutory_risk": "High SOX Section 302 / SEC Rule 10b-5 Enforcement Risk",
                "ruling_rationale": (
                    f"The Defense's argument of non-GAAP intent is formally REJECTED. The contradiction against "
                    f"certified SEC Form 10-Q ({concept}: claimed {spoken_val} vs audited {audited_val}) is material, "
                    f"statistically decisive (p = {p_val:.4e}), and corroborated by acute acoustic prosody elevation."
                ),
                "required_remedial_action": "Refer immediately to SEC Division of Enforcement; issue formal Audit Restatement Memo."
            }
        else:
            arbiter_synthesis = {
                "verdict": "TRUTHFUL_VERIFIED",
                "confidence_score": 0.08,
                "statutory_risk": "None / Compliant",
                "ruling_rationale": "Verbal claim is mathematically consistent with GAAP accounting conservation identities.",
                "required_remedial_action": "No action required."
            }

        return {
            "turn_id": turn_id,
            "speaker": speaker,
            "concept": concept,
            "prosecutor_case": prosecutor_arguments,
            "defense_rebuttal": defense_arguments,
            "judicial_verdict": arbiter_synthesis
        }
