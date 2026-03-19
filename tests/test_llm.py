from unittest.mock import patch

import pytest

from research_graph.config import LLMConfig


def test_create_llm_anthropic():
    from research_graph.llm import create_llm

    config = LLMConfig(provider="anthropic", model="claude-sonnet-4-20250514", temperature=0.3)
    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
        llm = create_llm(config)
    assert llm.model == "claude-sonnet-4-20250514"


def test_create_llm_openai():
    from research_graph.llm import create_llm

    config = LLMConfig(provider="openai", model="gpt-4o", temperature=0.3)
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        llm = create_llm(config)
    assert "gpt-4o" in llm.model_name


def test_create_llm_invalid_provider():
    from research_graph.llm import create_llm

    config = LLMConfig(provider="invalid", model="model", temperature=0.3)
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        create_llm(config)
