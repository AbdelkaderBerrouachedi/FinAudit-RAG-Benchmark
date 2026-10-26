"""
Audio & Acoustic Prosodic Analysis Engine.
Extracts voice-stress biomarkers (F0 elevation, pitch variance, jitter, shimmer,
and hesitation latency) to compute an acoustic dissonance metric S_prosody.
"""

from typing import Dict, Any, List
import math

class AudioProsodyAnalyzer:
    """
    Analyzes acoustic features extracted from earnings call audio waveforms.
    """
    def __init__(self,
                 jitter_threshold: float = 1.80,    # % threshold indicating micro-tremor
                 shimmer_threshold: float = 0.85,   # dB threshold indicating vocal tension
                 hesitation_threshold: float = 1.20 # seconds threshold indicating evasive latency
                 ):
        self.jitter_threshold = jitter_threshold
        self.shimmer_threshold = shimmer_threshold
        self.hesitation_threshold = hesitation_threshold

    def evaluate_utterance_prosody(self, prosody_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates acoustic metrics and computes a calibrated acoustic dissonance score in [0, 1].
        """
        f0_mean = prosody_data.get("f0_mean_hz", 120.0)
        f0_var = prosody_data.get("f0_variance", 10.0)
        jitter = prosody_data.get("jitter_pct", 0.8)
        shimmer = prosody_data.get("shimmer_db", 0.4)
        hesitation = prosody_data.get("hesitation_pause_sec", 0.2)
        speech_rate = prosody_data.get("speech_rate_wpm", 140.0)

        # 1. Jitter component (sigmoid activation above threshold)
        jitter_score = 1.0 / (1.0 + math.exp(-2.5 * (jitter - self.jitter_threshold)))

        # 2. Shimmer component
        shimmer_score = 1.0 / (1.0 + math.exp(-3.0 * (shimmer - self.shimmer_threshold)))

        # 3. Hesitation Latency component
        hesitation_score = min(1.0, max(0.0, (hesitation - 0.2) / (self.hesitation_threshold + 0.5)))

        # 4. F0 Variance elevation component
        f0_elev_score = min(1.0, max(0.0, (f0_var - 15.0) / 45.0))

        # Composite Dissonance Index (weighted average)
        # S_prosody = 0.35 * Jitter + 0.25 * Shimmer + 0.25 * Hesitation + 0.15 * F0_Elev
        composite_score = (
            0.35 * jitter_score +
            0.25 * shimmer_score +
            0.25 * hesitation_score +
            0.15 * f0_elev_score
        )
        composite_score = round(min(1.0, max(0.0, composite_score)), 4)

        is_dissonant = composite_score >= 0.60

        return {
            "f0_mean_hz": f0_mean,
            "f0_variance": f0_var,
            "jitter_pct": jitter,
            "shimmer_db": shimmer,
            "hesitation_pause_sec": hesitation,
            "speech_rate_wpm": speech_rate,
            "composite_prosody_score": composite_score,
            "is_acoustically_dissonant": is_dissonant,
            "diagnostic_flags": [
                flag for flag, active in [
                    ("High Vocal Jitter (Micro-tremor)", jitter >= self.jitter_threshold),
                    ("High Vocal Shimmer (Tension)", shimmer >= self.shimmer_threshold),
                    ("Prolonged Hesitation Latency", hesitation >= self.hesitation_threshold),
                    ("Abnormal F0 Instability", f0_var >= 40.0)
                ] if active
            ]
        }

    def process_transcript_turns(self, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Processes all transcript turns and enriches them with acoustic diagnostics."""
        enriched = []
        for turn in turns:
            raw_prosody = turn.get("acoustic_prosody", {})
            diag = self.evaluate_utterance_prosody(raw_prosody)
            turn_copy = dict(turn)
            turn_copy["acoustic_diagnostics"] = diag
            enriched.append(turn_copy)
        return enriched
