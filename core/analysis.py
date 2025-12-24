# pylint: disable=C0301, C0304, C0303
"""
Advanced analysis engine for HandyOsint.
"""

import logging
from collections import defaultdict
from typing import Any, Dict, List, Tuple

from config.platforms import PLATFORM_CATEGORIES, PLATFORM_INFO
from core.cache import CacheManager
from core.models import CorrelationData, PlatformResult, RiskLevel, ScanAnalysis

logger = logging.getLogger(__name__)


class AdvancedAnalysisEngine:
    """Machine learning and pattern analysis."""

    def __init__(self) -> None:
        """Initialize analysis engine."""
        self.cache = CacheManager()
        logger.info("Advanced Analysis Engine initialized")

    def calculate_risk_score(self, analysis: ScanAnalysis) -> Tuple[float, RiskLevel]:
        """Calculate comprehensive risk score."""
        if not analysis.platforms:
            return 0.0, RiskLevel.LOW

        risk_factors = []

        # Factor 1: Number of public profiles
        public_count = sum(
            1
            for p in analysis.platforms.values()
            if PLATFORM_INFO.get(p.platform_id, {}).get("audience") == "public"
            and p.found
        )
        public_risk = min(public_count * 0.15, 0.6)
        risk_factors.append(public_risk)

        # Factor 2: Platform risk scores
        platform_risks = []
        for result in analysis.platforms.values():
            if result.found:
                platform_info = PLATFORM_INFO.get(result.platform_id, {})
                platform_risks.append(platform_info.get("risk_score", 0.5))

        if platform_risks:
            avg_platform_risk = sum(platform_risks) / len(platform_risks)
            risk_factors.append(avg_platform_risk * 0.4)

        # Factor 3: Coverage across categories
        category_coverage = self._calculate_category_coverage(analysis.platforms)
        risk_factors.append(category_coverage * 0.25)

        # Factor 4: Data exposure breadth
        exposure_risk = self._calculate_exposure_risk(analysis.platforms)
        risk_factors.append(exposure_risk * 0.2)

        overall_score = sum(risk_factors) / len(risk_factors) if risk_factors else 0.0
        overall_score = min(overall_score, 1.0)

        # Determine risk level
        if overall_score >= 0.75:
            risk_level = RiskLevel.CRITICAL
        elif overall_score >= 0.60:
            risk_level = RiskLevel.HIGH
        elif overall_score >= 0.40:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        return round(overall_score, 3), risk_level

    def _calculate_category_coverage(
        self, platforms: Dict[str, PlatformResult]
    ) -> float:
        """Calculate coverage across platform categories."""
        found_categories = set()
        for result in platforms.values():
            if result.found:
                platform_info = PLATFORM_INFO.get(result.platform_id, {})
                category = platform_info.get("category")
                if category:
                    found_categories.add(category)

        return len(found_categories) / len(PLATFORM_CATEGORIES)

    def _calculate_exposure_risk(self, platforms: Dict[str, PlatformResult]) -> float:
        """Calculate data exposure risk."""
        total_exposure_items = 0
        for result in platforms.values():
            if result.found:
                platform_info = PLATFORM_INFO.get(result.platform_id, {})
                exposure = platform_info.get("data_exposure", [])
                total_exposure_items += len(exposure)

        max_possible_exposure = sum(
            len(p.get("data_exposure", [])) for p in PLATFORM_INFO.values()
        )

        return (
            total_exposure_items / max_possible_exposure
            if max_possible_exposure
            else 0.0
        )

    def analyze_correlations(self, analysis: ScanAnalysis) -> CorrelationData:
        """Perform correlation analysis."""
        cache_key = f"correlation:{analysis.username}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        correlation = CorrelationData(username=analysis.username)

        # Pattern detection
        correlation.common_patterns = self._detect_patterns(analysis.platforms)

        # Likelihood connections
        correlation.likely_connections = self._find_likely_connections(
            analysis.platforms
        )

        # Behavioral fingerprint
        correlation.behavioral_fingerprint = self._create_fingerprint(
            analysis.platforms
        )

        # Anomaly detection
        correlation.anomalies = self._detect_anomalies(analysis.platforms)

        # Confidence score
        correlation.confidence_score = self._calculate_confidence(correlation)

        self.cache.set(cache_key, correlation)
        return correlation

    def _detect_patterns(self, platforms: Dict[str, PlatformResult]) -> List[str]:
        """Detect common patterns in usernames/profiles."""
        patterns = []
        found_platforms = {p for p in platforms.values() if p.found}

        if len(found_platforms) >= 3:
            patterns.append("Multi-platform presence detected")

        category_counts = defaultdict(int)
        for result in found_platforms:
            platform_info = PLATFORM_INFO.get(result.platform_id, {})
            category = platform_info.get("category")
            if category:
                category_counts[category] += 1

        for category, count in category_counts.items():
            if count >= 2:
                cat_name = PLATFORM_CATEGORIES.get(category, {}).get("name", category)
                patterns.append(f"Strong presence in {cat_name} ({count} platforms)")

        return patterns

    def _find_likely_connections(
        self, platforms: Dict[str, PlatformResult]
    ) -> Dict[str, List[str]]:
        """Find likely connections between platforms."""
        connections = defaultdict(list)
        found_ids = {p.platform_id for p in platforms.values() if p.found}

        platform_pairs = [
            ("github", ["gitlab", "codepen", "stackoverflow"]),
            ("twitter", ["linkedin", "instagram", "reddit"]),
            ("youtube", ["twitch", "tiktok", "instagram"]),
            ("linkedin", ["twitter", "github"]),
        ]

        for primary, secondaries in platform_pairs:
            if primary in found_ids:
                connections[primary] = [s for s in secondaries if s in found_ids]

        return dict(connections)

    def _create_fingerprint(
        self, platforms: Dict[str, PlatformResult]
    ) -> Dict[str, Any]:
        """Create behavioral fingerprint."""
        fingerprint = {
            "platform_count": len([p for p in platforms.values() if p.found]),
            "primary_interest": self._identify_primary_interest(platforms),
            "activity_profile": self._analyze_activity_profile(platforms),
            "privacy_awareness": self._assess_privacy_awareness(platforms),
            "monetization_status": self._check_monetization(platforms),
        }
        return fingerprint

    def _identify_primary_interest(self, platforms: Dict[str, PlatformResult]) -> str:
        """Identify primary interest area."""
        category_counts = defaultdict(int)
        for result in platforms.values():
            if result.found:
                platform_info = PLATFORM_INFO.get(result.platform_id, {})
                category = platform_info.get("category")
                if category:
                    category_counts[category] += 1

        if not category_counts:
            return "unknown"

        primary = max(category_counts.items(), key=lambda x: x[1])
        return primary[0]

    def _analyze_activity_profile(self, platforms: Dict[str, PlatformResult]) -> str:
        """Analyze activity profile."""
        activity_types = defaultdict(int)
        for result in platforms.values():
            if result.found:
                platform_info = PLATFORM_INFO.get(result.platform_id, {})
                activity = platform_info.get("activity_type")
                if activity:
                    activity_types[activity] += 1

        if not activity_types:
            return "inactive"

        if len(activity_types) >= 4:
            return "highly_diverse"
        if len(activity_types) >= 2:
            return "multi_interest"
        return "specialized"

    def _assess_privacy_awareness(self, platforms: Dict[str, PlatformResult]) -> str:
        """Assess privacy awareness."""
        configurable_count = sum(
            1
            for p in platforms.values()
            if p.found
            and PLATFORM_INFO.get(p.platform_id, {}).get("audience") == "configurable"
        )

        private_count = sum(
            1
            for p in platforms.values()
            if p.found
            and PLATFORM_INFO.get(p.platform_id, {}).get("audience") != "public"
        )

        total_found = sum(1 for p in platforms.values() if p.found)

        if total_found == 0:
            return "not_applicable"

        privacy_ratio = (private_count + configurable_count) / total_found

        if privacy_ratio > 0.7:
            return "privacy_conscious"
        if privacy_ratio < 0.3:
            return "privacy_negligent"
        return "average"

    def _check_monetization(self, platforms: Dict[str, PlatformResult]) -> str:
        """Check monetization presence."""
        monetization_platforms = ["patreon", "youtube", "twitch", "medium"]
        found_monetization = [
            p
            for p in platforms.values()
            if p.found and p.platform_id in monetization_platforms
        ]

        if len(found_monetization) >= 2:
            return "active_monetization"
        if len(found_monetization) == 1:
            return "partial_monetization"
        return "no_monetization"

    def _detect_anomalies(self, platforms: Dict[str, PlatformResult]) -> List[str]:
        """Detect anomalies in profile data."""
        anomalies = []

        response_times = [p.response_time for p in platforms.values() if p.found]
        if response_times:
            avg_time = sum(response_times) / len(response_times)
            slow_platforms = [
                p.platform_name
                for p in platforms.values()
                if p.found and p.response_time > avg_time * 2
            ]
            if slow_platforms:
                anomalies.append(f"Slow response from: {', '.join(slow_platforms)}")

        mixed_statuses = any(p.status == "blocked" for p in platforms.values())
        if mixed_statuses:
            anomalies.append("Profile blocking detected - possible account restriction")

        return anomalies

    def _calculate_confidence(self, correlation: CorrelationData) -> float:
        """Calculate overall confidence score."""
        score = 0.0

        if correlation.common_patterns:
            score += 0.3 * min(len(correlation.common_patterns) / 3, 1.0)

        if correlation.likely_connections:
            score += 0.4 * min(len(correlation.likely_connections) / 5, 1.0)

        if correlation.behavioral_fingerprint.get("platform_count", 0) > 1:
            score += 0.3

        return min(round(score, 2), 1.0)
