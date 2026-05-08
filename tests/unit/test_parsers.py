"""Tests for prompt format parsers — round-trip: parse → serialize → parse."""

import json
from pathlib import Path

from pgit.parsers import detect_format, parse
from pgit.parsers.json_messages import parse as parse_json, serialize as serialize_json
from pgit.parsers.plaintext import parse as parse_plain, serialize as serialize_plain
from pgit.parsers.yaml_turns import parse as parse_yaml, serialize as serialize_yaml

FIXTURES = Path(__file__).parent.parent / "fixtures" / "prompts"


class TestDetectFormat:
    def test_markdown(self):
        assert detect_format("system.md") == "plaintext"

    def test_txt(self):
        assert detect_format("prompt.txt") == "plaintext"

    def test_jinja2(self):
        assert detect_format("template.j2") == "jinja2"

    def test_json(self):
        assert detect_format("messages.json") == "json_messages"

    def test_yaml(self):
        assert detect_format("turns.yaml") == "yaml_turns"

    def test_yml(self):
        assert detect_format("turns.yml") == "yaml_turns"

    def test_unknown(self):
        assert detect_format("data.csv") == "plaintext"


class TestPlaintextParser:
    def test_parse_fixture(self):
        content = (FIXTURES / "system.md").read_text()
        segments = parse_plain(content)
        assert len(segments) > 1  # Should have multiple paragraphs

    def test_roundtrip(self):
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        segments = parse_plain(content)
        restored = serialize_plain(segments)
        re_parsed = parse_plain(restored)
        assert segments == re_parsed


class TestJsonMessagesParser:
    def test_parse_fixture(self):
        content = (FIXTURES / "messages.json").read_text()
        segments = parse_json(content)
        assert len(segments) == 3
        assert segments[0].startswith("[system]")

    def test_roundtrip(self):
        content = (FIXTURES / "messages.json").read_text()
        segments = parse_json(content)
        restored = serialize_json(segments)
        re_parsed = parse_json(restored)
        assert segments == re_parsed


class TestYamlTurnsParser:
    def test_parse_fixture(self):
        content = (FIXTURES / "turns.yaml").read_text()
        segments = parse_yaml(content)
        assert len(segments) == 3
        assert segments[0].startswith("[system]")

    def test_roundtrip(self):
        content = (FIXTURES / "turns.yaml").read_text()
        segments = parse_yaml(content)
        restored = serialize_yaml(segments)
        re_parsed = parse_yaml(restored)
        assert segments == re_parsed


class TestJinja2Parser:
    def test_parse_fixture(self):
        content = (FIXTURES / "template.j2").read_text()
        from pgit.parsers.jinja2 import parse as parse_j2
        segments = parse_j2(content)
        assert len(segments) > 1  # Has block-level tags
