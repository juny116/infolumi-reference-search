"""Offline memory behavior tests; model and search-service clients are mocked."""

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class Message:
    def __init__(self, content, additional_kwargs=None):
        self.content = content
        self.additional_kwargs = additional_kwargs or {}


class HumanMessage(Message):
    pass


class AIMessage(Message):
    pass


class SystemMessage(Message):
    pass


class SearchClient:
    def __init__(self, host):
        self.indices = types.SimpleNamespace(exists=lambda **kw: True)


def load_memory():
    schema = types.ModuleType("langchain.schema")
    for name, value in {
        "AIMessage": AIMessage,
        "HumanMessage": HumanMessage,
        "SystemMessage": SystemMessage,
        "BaseMessage": Message,
        "BaseChatMessageHistory": object,
    }.items():
        setattr(schema, name, value)
    elastic = types.ModuleType("elasticsearch")
    elastic.Elasticsearch = SearchClient
    modules = {
        "langchain": types.ModuleType("langchain"),
        "langchain.schema": schema,
        "elasticsearch": elastic,
    }
    spec = importlib.util.spec_from_file_location(
        "memory_under_test",
        Path(__file__).resolve().parents[1]
        / "infolumi"
        / "extras"
        / "conversation_memory.py",
    )
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.module = load_memory()

    def context(self):
        import inspect

        cls = self.module.ChatMessageHistoryWithContextWindow
        history = (
            cls(window_size=8)
            if "window_size" in inspect.signature(cls).parameters
            else cls()
        )
        history.window_size = 8
        return history

    def long_term(self):
        import inspect

        cls = self.module.ChatMessageHistoryWithLongTerm
        if "window_size" in inspect.signature(cls).parameters:
            return cls("localhost:9200", "conversation", 8, 4)
        return cls("localhost:9200", "conversation")

    def test_instances_do_not_share_messages(self):
        first, second = self.context(), self.context()
        first.add_user_message("first conversation", 2)
        self.assertEqual(second.messages, [])
        self.assertIsNot(first.messages, second.messages)

    def test_empty_and_cleared_context(self):
        history = self.context()
        self.assertEqual(history.get_messages_within_window_size(), [])
        history.add_user_message("hello", 2)
        history.clear()
        self.assertEqual(history.get_messages_within_window_size(), [])

    def test_window_keeps_system_and_recent_messages(self):
        history = self.context()
        history.set_system_message(SystemMessage("system", {"token_length": 2}))
        history.add_user_message("old", 4)
        history.add_ai_message("recent", 4)
        self.assertEqual(
            [m.content for m in history.get_messages_within_window_size()],
            ["system", "recent"],
        )

    def test_long_term_constructs_and_empty_history_skips_search(self):
        history = self.long_term()
        history._get_long_term = lambda _: self.fail("empty history must not search")
        self.assertEqual(history.get_messages_with_long_term(), [])
        self.assertEqual(history.current_length, 0)

    def test_pipe_characters_survive_history_roundtrip(self):
        history = self.long_term()
        history.set_system_message(SystemMessage("system", {"token_length": 1}))
        history.add_user_message("a|b|c", 1)
        history.add_ai_message("x|y", 1)
        saved = []
        history._insertData = lambda index, key, log: saved.append(log)
        history._save_long_term()
        history._getData = lambda index, query: saved[0]
        restored = history._get_long_term("query")
        self.assertEqual([m.content for m in restored], ["a|b|c", "x|y"])


if __name__ == "__main__":
    unittest.main()
