#!/usr/bin/env python3
"""Unit tests for the Geo Answer Key parser helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_DIR))

from app import build_demo_answer_key, extract_text, parse_json_block


class GeoAnswerKeyParsingTests(unittest.TestCase):
    def test_build_demo_answer_key_is_deterministic_for_filename(self) -> None:
        first = build_demo_answer_key("sample-road.jpg")
        second = build_demo_answer_key("sample-road.jpg")
        self.assertEqual(first["location_name"], second["location_name"])
        self.assertEqual(first["mode"], "demo")

    def test_extract_text_reads_message_content(self) -> None:
        payload = {
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": '{"location_name":"Lisbon"}'},
                    ],
                }
            ]
        }

        self.assertEqual(extract_text(payload), '{"location_name":"Lisbon"}')

    def test_extract_text_uses_output_text_fallback(self) -> None:
        payload = {"output_text": '{"location_name":"Tokyo"}'}
        self.assertEqual(extract_text(payload), '{"location_name":"Tokyo"}')

    def test_parse_json_block_handles_markdown_fences(self) -> None:
        raw_text = '```json\n{"location_name":"Reykjavik"}\n```'
        parsed = parse_json_block(raw_text)
        self.assertEqual(parsed["location_name"], "Reykjavik")

    def test_parse_json_block_finds_json_inside_extra_text(self) -> None:
        raw_text = 'Best guess:\n{"location_name":"Cusco","confidence":"medium"}\nThanks.'
        parsed = parse_json_block(raw_text)
        self.assertEqual(parsed["location_name"], "Cusco")
        self.assertEqual(parsed["confidence"], "medium")


if __name__ == "__main__":
    unittest.main()
