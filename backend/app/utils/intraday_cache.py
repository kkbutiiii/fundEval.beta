"""
Intraday valuation cache for storing real-time valuation samples.
Uses a simple in-memory cache with a maximum number of data points.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class ValuationPoint:
    """A single valuation data point."""
    time: str
    estimated_nav: float
    estimated_change_percent: float
    timestamp: datetime = field(default_factory=datetime.now)


class IntradayCache:
    """Cache for intraday valuation history."""

    def __init__(self, max_points: int = 480):  # 4 hours of 30-second samples
        self._cache: Dict[str, List[ValuationPoint]] = {}
        self._max_points = max_points
        self._lock = Lock()

    def add_sample(self, fund_code: str, estimated_nav: float, estimated_change_percent: float) -> None:
        """
        Add a new valuation sample.

        Args:
            fund_code: Fund code
            estimated_nav: Estimated NAV
            estimated_change_percent: Estimated change percent
        """
        with self._lock:
            if fund_code not in self._cache:
                self._cache[fund_code] = []

            now = datetime.now()
            time_str = now.strftime("%H:%M:%S")

            point = ValuationPoint(
                time=time_str,
                estimated_nav=estimated_nav,
                estimated_change_percent=estimated_change_percent,
                timestamp=now
            )

            self._cache[fund_code].append(point)

            # Trim old data
            if len(self._cache[fund_code]) > self._max_points:
                self._cache[fund_code] = self._cache[fund_code][-self._max_points:]

    def get_history(self, fund_code: str) -> List[ValuationPoint]:
        """
        Get intraday valuation history for a fund.

        Args:
            fund_code: Fund code

        Returns:
            List of ValuationPoint objects
        """
        with self._lock:
            # Return a copy to avoid modification
            return list(self._cache.get(fund_code, []))

    def clear_fund(self, fund_code: str) -> None:
        """Clear cache for a specific fund."""
        with self._lock:
            if fund_code in self._cache:
                del self._cache[fund_code]

    def clear_all(self) -> None:
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()

    def cleanup_old_data(self, max_age_minutes: int = 300) -> None:
        """
        Remove data older than specified age.

        Args:
            max_age_minutes: Maximum age in minutes (default 5 hours)
        """
        cutoff = datetime.now() - timedelta(minutes=max_age_minutes)

        with self._lock:
            for fund_code in list(self._cache.keys()):
                self._cache[fund_code] = [
                    p for p in self._cache[fund_code]
                    if p.timestamp > cutoff
                ]

                if not self._cache[fund_code]:
                    del self._cache[fund_code]


# Singleton instance
intraday_cache = IntradayCache()
