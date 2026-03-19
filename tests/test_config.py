def test_load_config_from_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(
        """
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  temperature: 0.3
research:
  max_cycles: 5
  max_sources_per_query: 5
report:
  output_dir: "./reports"
mcp:
  server_url: ""
  transport: "stdio"
"""
    )
    from research_graph.config import load_config

    config = load_config(str(config_file))
    assert config.llm.provider == "anthropic"
    assert config.llm.model == "claude-sonnet-4-20250514"
    assert config.llm.temperature == 0.3
    assert config.research.max_cycles == 5
    assert config.research.max_sources_per_query == 5
    assert config.report.output_dir == "./reports"
    assert config.mcp.server_url == ""
    assert config.mcp.transport == "stdio"


def test_load_config_default_path():
    from research_graph.config import load_config

    config = load_config()
    assert config.llm.provider is not None
