from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

_DEFAULT_CONFIG_PATH = "config.yaml"


@dataclass
class LLMConfig:
    provider: str = "anthropic"
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.3


@dataclass
class ResearchConfig:
    max_cycles: int = 5
    max_sources_per_query: int = 5


@dataclass
class ReportConfig:
    output_dir: str = "./reports"


@dataclass
class MCPConfig:
    server_url: str = ""
    transport: str = "stdio"


@dataclass
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    research: ResearchConfig = field(default_factory=ResearchConfig)
    report: ReportConfig = field(default_factory=ReportConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)


def load_config(config_path: str | None = None) -> AppConfig:
    load_dotenv()
    path = Path(config_path or _DEFAULT_CONFIG_PATH)
    if not path.exists():
        return AppConfig()
    raw = yaml.safe_load(path.read_text()) or {}
    return AppConfig(
        llm=LLMConfig(**raw.get("llm", {})),
        research=ResearchConfig(**raw.get("research", {})),
        report=ReportConfig(**raw.get("report", {})),
        mcp=MCPConfig(**raw.get("mcp", {})),
    )
