"""
Tone Analyzer - Formality and Urgency Detection

Provides production-ready tone analysis for query formality, urgency,
and user expertise level detection.

Features:
- Formality level detection (5 levels)
- Urgency marker detection (4 levels)
- User expertise inference
- Pattern-based analysis with confidence scores

Usage:
    analyzer = ToneAnalyzer()
    tone = await analyzer.analyze("URGENT: Production system is down!")
    print(tone.urgency)  # UrgencyLevel.CRITICAL
"""

import logging
import re
from typing import Dict, List, Tuple

from app.rag_consultation.models import (
    ToneAnalysis,
    FormalityLevel,
    UrgencyLevel,
    ExpertiseLevel,
)

logger = logging.getLogger(__name__)


class ToneAnalyzer:
    """Tone and communication style analyzer.

    Analyzes query tone for formality, urgency, and expertise level
    using pattern matching and linguistic markers.

    Attributes:
        formality_markers: Patterns for formality detection
        urgency_markers: Patterns for urgency detection
        expertise_markers: Patterns for expertise detection
    """

    # Formality indicators
    FORMAL_MARKERS = [
        r"\b(kindly|please|would you|could you|may I|thank you)\b",
        r"\b(request|require|appreciate|grateful)\b",
        r"\b(sir|madam|dear|esteemed)\b",
    ]

    CASUAL_MARKERS = [
        r"\b(hey|hi|yo|sup|yeah|nope|gonna|wanna)\b",
        r"\b(cool|awesome|great|nice|sweet)\b",
        r"\b(btw|fyi|asap|lol|thx)\b",
        r"[!]{2,}",  # Multiple exclamation marks
    ]

    # Urgency indicators
    CRITICAL_MARKERS = [
        r"\b(urgent|critical|emergency|asap|immediately|now)\b",
        r"\b(production|live|down|outage|breaking|failed)\b",
        r"[!]{2,}",  # Multiple exclamation marks
    ]

    HIGH_URGENCY_MARKERS = [
        r"\b(important|priority|quick|fast|soon|urgent)\b",
        r"\b(deadline|time-sensitive|hurry)\b",
    ]

    MEDIUM_URGENCY_MARKERS = [
        r"\b(when|how long|timeline|schedule)\b",
        r"\b(need|want|would like)\b",
    ]

    # Expertise indicators
    BEGINNER_MARKERS = [
        r"\b(new to|beginner|just started|learning|don't know|confused)\b",
        r"\b(what is|what are|how do I|help me understand)\b",
        r"\b(simple|basic|easy|explain like)\b",
    ]

    EXPERT_MARKERS = [
        r"\b(implementation|architecture|optimization|scalability)\b",
        r"\b(performance|latency|throughput|benchmark)\b",
        r"\b(distributed|concurrent|async|microservice)\b",
        r"\b(protocol|algorithm|complexity|trade-off)\b",
    ]

    def __init__(self) -> None:
        """Initialize tone analyzer."""
        logger.info("Tone analyzer initialized")

    def _count_matches(self, query: str, patterns: List[str]) -> int:
        """Count pattern matches in query.

        Args:
            query: User query
            patterns: List of regex patterns

        Returns:
            Number of pattern matches
        """
        query_lower = query.lower()
        matches = 0
        for pattern in patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                matches += 1
        return matches

    def _analyze_formality(self, query: str) -> Tuple[FormalityLevel, float]:
        """Analyze query formality level.

        Args:
            query: User query

        Returns:
            Tuple of (formality level, confidence score)
        """
        formal_count = self._count_matches(query, self.FORMAL_MARKERS)
        casual_count = self._count_matches(query, self.CASUAL_MARKERS)

        # Calculate formality score (-1 to 1)
        if formal_count + casual_count == 0:
            return FormalityLevel.NEUTRAL, 0.5

        formality_score = (formal_count - casual_count) / (
            formal_count + casual_count
        )

        # Map score to formality level
        if formality_score > 0.5:
            level = FormalityLevel.VERY_FORMAL
        elif formality_score > 0.0:
            level = FormalityLevel.FORMAL
        elif formality_score > -0.5:
            level = FormalityLevel.NEUTRAL
        elif formality_score > -0.8:
            level = FormalityLevel.CASUAL
        else:
            level = FormalityLevel.VERY_CASUAL

        confidence = abs(formality_score)
        return level, confidence

    def _analyze_urgency(self, query: str) -> Tuple[UrgencyLevel, List[str]]:
        """Analyze query urgency level.

        Args:
            query: User query

        Returns:
            Tuple of (urgency level, detected urgency markers)
        """
        critical_matches = self._count_matches(query, self.CRITICAL_MARKERS)
        high_matches = self._count_matches(query, self.HIGH_URGENCY_MARKERS)
        medium_matches = self._count_matches(query, self.MEDIUM_URGENCY_MARKERS)

        # Collect matched markers
        markers = []
        query_lower = query.lower()

        for pattern in self.CRITICAL_MARKERS + self.HIGH_URGENCY_MARKERS:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                markers.append(match.group())

        # Determine urgency level
        if critical_matches > 0:
            level = UrgencyLevel.CRITICAL
        elif high_matches > 0:
            level = UrgencyLevel.HIGH
        elif medium_matches > 0:
            level = UrgencyLevel.MEDIUM
        else:
            level = UrgencyLevel.LOW

        return level, markers

    def _analyze_expertise(self, query: str) -> ExpertiseLevel:
        """Infer user expertise level from query.

        Args:
            query: User query

        Returns:
            Inferred expertise level
        """
        beginner_count = self._count_matches(query, self.BEGINNER_MARKERS)
        expert_count = self._count_matches(query, self.EXPERT_MARKERS)

        # Calculate expertise score
        total_markers = beginner_count + expert_count

        if total_markers == 0:
            return ExpertiseLevel.INTERMEDIATE

        expertise_ratio = expert_count / total_markers

        if expertise_ratio > 0.7:
            return ExpertiseLevel.EXPERT
        elif expertise_ratio > 0.4:
            return ExpertiseLevel.ADVANCED
        elif beginner_count > expert_count:
            return ExpertiseLevel.BEGINNER
        else:
            return ExpertiseLevel.INTERMEDIATE

    async def analyze(self, query: str) -> ToneAnalysis:
        """Analyze query tone and communication style.

        Args:
            query: User query string

        Returns:
            ToneAnalysis with formality, urgency, and expertise

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        query = query.strip()

        try:
            # Analyze formality
            formality, formality_score = self._analyze_formality(query)

            # Analyze urgency
            urgency, urgency_markers = self._analyze_urgency(query)

            # Analyze expertise
            expertise = self._analyze_expertise(query)

            analysis = ToneAnalysis(
                formality=formality,
                urgency=urgency,
                expertise_level=expertise,
                formality_score=formality_score,
                urgency_markers=urgency_markers,
            )

            logger.info(
                f"Tone analysis: formality={formality.value}, "
                f"urgency={urgency.value}, expertise={expertise.value}"
            )

            return analysis

        except Exception as e:
            logger.error(f"Tone analysis failed: {e}")
            raise RuntimeError(f"Analysis error: {e}") from e
