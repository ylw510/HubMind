"""
Simple smoke tests for the multi-agent SupervisorAgent.

These tests do NOT assert on concrete GitHub / LLM results (which depend on
network and tokens). Instead, they verify that:

- SupervisorAgent can be constructed with override tokens.
- The LangGraph-based chat pipeline returns a string response for each
  of the main intents:
    - project discovery
    - issue listing
    - PR analysis (batch and single-PR)

Run manually:

    backend/venv/bin/python -m tests.chat_smoke_tests
"""
from __future__ import annotations

import unittest

from src.agents.supervisor_agent import SupervisorAgent


def make_test_agent() -> SupervisorAgent:
    """
    Create a SupervisorAgent instance for tests.

    We pass dummy github_token / llm_api_key so that Config.validate() is
    skipped and construction does not depend on local env variables.
    Real network calls may still fail internally, but the graph nodes are
    written to catch exceptions and turn them into error payloads.
    """
    return SupervisorAgent(
        provider="deepseek",
        github_token="test-token",
        llm_api_key="test-llm-key",
    )


class ChatSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.agent = make_test_agent()

    def _assert_response_ok(self, prompt: str) -> None:
        resp = self.agent.chat(prompt, [])
        self.assertIsInstance(resp, str)
        # Response should not be trivially empty
        self.assertGreater(len(resp.strip()), 0, msg=f"Empty response for: {prompt!r}")

    def test_project_discovery_intent(self) -> None:
        prompt = "我想做一个 AI 相关的开源项目调研，给我推荐最近一周最火的 5 个项目"
        self._assert_response_ok(prompt)

    def test_issue_self_intent(self) -> None:
        prompt = "帮我看看我自己仓库 owner/repo 最近的 open issue，有哪些优先处理的？"
        self._assert_response_ok(prompt)

    def test_issue_other_intent(self) -> None:
        prompt = "我想在别人仓库 microsoft/vscode 里接一些 good first issue，帮我列一下 open 的 issue"
        self._assert_response_ok(prompt)

    def test_pr_batch_analysis_intent(self) -> None:
        prompt = "帮我分析一下 ClickHouse/ClickHouse 最近一周和内存相关的 PR，总结出最有价值的 5 个 PR"
        self._assert_response_ok(prompt)

    def test_pr_single_analysis_intent(self) -> None:
        prompt = "请分析一下 ClickHouse/ClickHouse 仓库中 PR #123 的改动和风险"
        self._assert_response_ok(prompt)


if __name__ == "__main__":
    unittest.main()

