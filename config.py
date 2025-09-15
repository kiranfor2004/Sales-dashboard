"""Central configuration for Sales Dashboard.

This module provides:
- Data path resolution across local and Azure environments
- Feature flags
- Logging configuration primitives
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from typing import List


def _default_data_paths() -> List[str]:
    base = os.getcwd()
    here = os.path.dirname(__file__)
    candidates = [
        'Sales data - Filtered',
        './Sales data - Filtered',
        os.path.join(base, 'Sales data - Filtered'),
        os.path.join(here, 'Sales data - Filtered'),
        '/home/site/wwwroot/Sales data - Filtered',
        '/home/site/wwwroot/backend/Sales data - Filtered',
    ]
    return candidates

@dataclass(frozen=True)
class FeatureFlags:
    ENABLE_STATS: bool = True
    ENABLE_REFRESH: bool = True
    ENABLE_VERBOSE_LOG: bool = bool(int(os.getenv('VERBOSE_LOG', '0')))

@dataclass
class AppConfig:
    ENV: str = os.getenv('APP_ENV', 'production')
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO').upper()
    DATA_FILE_CANDIDATES: List[str] = None  # type: ignore
    FEATURE_FLAGS: FeatureFlags = FeatureFlags()

    def __post_init__(self):
        if self.DATA_FILE_CANDIDATES is None:
            self.DATA_FILE_CANDIDATES = _default_data_paths()

CONFIG = AppConfig()

