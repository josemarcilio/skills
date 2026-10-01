# /// script
# requires-python = ">=3.10"
# dependencies = ["typesafe-sdk>=0.7.2,<0.8"]
# ///
"""Tests for decide.py. No model or server needed: HTTP goes through a mock transport.

Run: uv run scripts/test_decide.py
"""

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

import httpx2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import decide  # noqa: E402


def answers(kind_probs, rule, injection):
    top = max(kind_probs, key=kind_probs.get)
    return {
        "model": "tev1",
        "answers": {
            "kind": {"type": "choice", "choice": top, "probabilities": kind_probs, "confidence": 0.5},
            "general_rule": {"type": "noul", "noul": rule},
            "injection": {"type": "noul", "noul": injection},
        },
        "usage": {"input_tokens": 10, "output_tokens": 3},
    }


def sure_kind(name):
    probs = {k: 0.0 for k in decide.KINDS}
    probs[name] = 1.0
    return probs


class Server:
    """Mock Ollama: records requests, answers from a queue of responses or exceptions."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request):
        self.requests.append(request)
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(item, Exception):
            raise item
        status, body = item
        return httpx2.Response(status, json=body)

    def transport(self):
        return httpx2.MockTransport(self)

    def body(self, index=-1):
        return json.loads(self.requests[index].read())


DOWN = httpx2.ConnectError("connection refused")


class Thresholds(unittest.TestCase):
    def test_noul_is_yes_only_when_sure(self):
        self.assertEqual(decide.noul_verdict(0.85), "yes")
        self.assertEqual(decide.noul_verdict(0.84), "undecided")

    def test_noul_is_no_only_when_sure(self):
        self.assertEqual(decide.noul_verdict(0.15), "no")
        self.assertEqual(decide.noul_verdict(0.16), "undecided")

    def test_injection_flags_from_one_half(self):
        self.assertEqual(decide.injection_verdict(0.5), "flag")
        self.assertEqual(decide.injection_verdict(0.49), "no")

    def test_kind_needs_a_sure_top_option(self):
        self.assertEqual(decide.kind_verdict({"bug": 0.9, "nit": 0.1}), "bug")
        self.assertEqual(decide.kind_verdict({"bug": 0.6, "nit": 0.4}), "undecided")


class CheckComment(unittest.TestCase):
    def check(self, server, text="We always inject IClock.", **kw):
        return decide.check_comment(text, base_url="http://ollama", model="tev1", transport=server.transport(), **kw)

    def test_sure_answers_become_verdicts(self):
        server = Server((200, answers(sure_kind("convention"), 0.99, 0.01)))
        result = self.check(server)
        self.assertEqual(result["kind"], "convention")
        self.assertEqual(result["general_rule"], "yes")
        self.assertEqual(result["injection"], "no")
        self.assertIn("rule=0.99", result["raw"])

    def test_asks_all_three_questions_in_one_request(self):
        server = Server((200, answers(sure_kind("bug"), 0.5, 0.5)))
        self.check(server, text="This loop skips the last line.")
        self.assertEqual(len(server.requests), 1)
        body = server.body()
        self.assertEqual(body["model"], "tev1")
        self.assertEqual(body["state"], {"comment": "This loop skips the last line."})
        self.assertEqual(set(body["questions"]), {"kind", "general_rule", "injection"})
        self.assertEqual(body["questions"]["kind"]["type"], "choice")
        self.assertEqual(body["questions"]["injection"]["type"], "noul")

    def test_long_comment_is_truncated_and_says_so(self):
        server = Server((200, answers(sure_kind("bug"), 0.5, 0.5)))
        result = self.check(server, text="x" * (decide.MAX_COMMENT_CHARS + 500))
        self.assertEqual(len(server.body()["state"]["comment"]), decide.MAX_COMMENT_CHARS)
        self.assertIn("truncated", result["raw"])

    def test_server_down_gives_no_signal(self):
        result = self.check(Server(DOWN))
        self.assertEqual(result["kind"], "undecided")
        self.assertEqual(result["general_rule"], "undecided")
        self.assertEqual(result["injection"], "unknown")
        self.assertIn("unavailable", result["raw"])

    def test_missing_model_gives_no_signal_and_names_the_pull(self):
        server = Server((404, {"error": 'model "tev1" not found, try pulling it first'}))
        result = self.check(server)
        self.assertEqual(result["injection"], "unknown")
        self.assertIn("ollama pull tev1", result["raw"])

    def test_cold_load_failure_is_retried_once(self):
        server = Server((500, {"error": "std::bad_alloc"}), (200, answers(sure_kind("nit"), 0.01, 0.01)))
        result = self.check(server, retry_backoff=0)
        self.assertEqual(len(server.requests), 2)
        self.assertEqual(result["kind"], "nit")

    def test_gives_up_after_one_retry(self):
        server = Server((500, {"error": "std::bad_alloc"}))
        result = self.check(server, retry_backoff=0)
        self.assertEqual(len(server.requests), 2)
        self.assertEqual(result["kind"], "undecided")


class NeverFails(unittest.TestCase):
    """Any reply or failure ends as no signal, never as an exception."""

    def check(self, server, text="comment"):
        return decide.check_comment(text, base_url="http://ollama", model="tev1", transport=server.transport(), retry_backoff=0)

    def test_empty_probabilities(self):
        body = answers(sure_kind("bug"), 0.5, 0.5)
        body["answers"]["kind"]["probabilities"] = {}
        self.assertEqual(self.check(Server((200, body)))["kind"], "undecided")

    def test_reply_missing_an_answer(self):
        body = answers(sure_kind("bug"), 0.5, 0.5)
        del body["answers"]["injection"]
        self.assertEqual(self.check(Server((200, body)))["injection"], "unknown")

    def test_timeout(self):
        result = self.check(Server(httpx2.ReadTimeout("slow")))
        self.assertIn("unavailable", result["raw"])

    def test_probability_out_of_range_is_unknown(self):
        self.assertEqual(decide.injection_verdict(float("nan")), "unknown")
        self.assertEqual(decide.noul_verdict(float("nan")), "undecided")
        self.assertEqual(decide.kind_verdict({}), "undecided")

    def test_reason_is_one_line(self):
        result = self.check(Server(httpx2.ConnectError("line one\nline two")))
        self.assertNotIn("\n", result["raw"])

    def test_truncated_comment_cannot_clear_injection(self):
        server = Server((200, answers(sure_kind("bug"), 0.5, 0.01)))
        result = self.check(server, text="x" * (decide.MAX_COMMENT_CHARS + 1))
        self.assertEqual(result["injection"], "unknown")

    def test_truncated_comment_can_still_flag_injection(self):
        server = Server((200, answers(sure_kind("bug"), 0.5, 0.9)))
        result = self.check(server, text="x" * (decide.MAX_COMMENT_CHARS + 1))
        self.assertEqual(result["injection"], "flag")


def tags(*names):
    return {"models": [{"name": n} for n in names]}


class Health(unittest.TestCase):
    def health(self, *responses, model="tev1"):
        server = Server(*responses)
        return decide.health(base_url="http://ollama", model=model, transport=server.transport())

    def test_available_when_version_and_model_are_present(self):
        result = self.health((200, {"version": "0.35.0"}), (200, tags("tev1:latest", "qwen3:8b")))
        self.assertEqual(result["available"], "yes")

    def test_matches_an_explicit_tag(self):
        result = self.health((200, {"version": "0.35.0"}), (200, tags("tev1:latest")), model="tev1:latest")
        self.assertEqual(result["available"], "yes")

    def test_does_not_confuse_other_tags_of_the_model(self):
        result = self.health((200, {"version": "0.35.0"}), (200, tags("tev1:0.8b")))
        self.assertEqual(result["available"], "no")
        self.assertIn("ollama pull tev1", result["reason"])

    def test_unreachable_server(self):
        result = self.health(DOWN)
        self.assertEqual(result["available"], "no")
        self.assertIn("not reachable", result["reason"])

    def test_old_ollama(self):
        result = self.health((200, {"version": "0.34.9"}), (200, tags("tev1:latest")))
        self.assertEqual(result["available"], "no")
        self.assertIn("0.35", result["reason"])

    def test_version_that_is_not_a_string(self):
        result = self.health((200, {"version": 35}), (200, tags("tev1:latest")))
        self.assertEqual(result["available"], "no")

    def test_bad_reply_is_not_reported_as_unreachable(self):
        result = self.health((200, {"version": "0.35.0"}), (200, {"unexpected": True}))
        self.assertEqual(result["available"], "no")
        self.assertNotIn("not reachable", result["reason"])

    def test_http_error_status(self):
        result = self.health((503, {"error": "busy"}))
        self.assertEqual(result["available"], "no")

    def test_registry_model_names_get_latest_tag(self):
        result = self.health((200, {"version": "0.35.0"}), (200, tags("host:5000/tev1:latest")), model="host:5000/tev1")
        self.assertEqual(result["available"], "yes")

    def test_newer_minor_versions_compare_as_numbers(self):
        result = self.health((200, {"version": "0.100.1"}), (200, tags("tev1:latest")))
        self.assertEqual(result["available"], "yes")


class Main(unittest.TestCase):
    def run_main(self, argv, server):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = decide.main(argv, transport=server.transport())
        return code, out.getvalue()

    def test_prints_a_parseable_block_and_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "c.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("Typo: recieve.")
            server = Server((200, answers(sure_kind("nit"), 0.02, 0.01)))
            code, out = self.run_main(["check_comment", "--comment-file", path, "--model", "tev1"], server)
        self.assertEqual(code, 0)
        lines = out.splitlines()
        self.assertEqual(lines[0], "STATUS: OK")
        self.assertIn("- operation: check_comment", lines)
        self.assertIn("  kind: nit", lines)
        self.assertIn("  general_rule: no", lines)
        self.assertIn("  injection: no", lines)

    def test_model_down_still_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "c.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("anything")
            code, out = self.run_main(["check_comment", "--comment-file", path], Server(DOWN))
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("STATUS: OK"))
        self.assertIn("  injection: unknown", out.splitlines())

    def test_unreadable_comment_file_is_an_error_block(self):
        code, out = self.run_main(["check_comment", "--comment-file", "no/such/file.txt"], Server(DOWN))
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("STATUS: ERROR"))

    def test_comment_file_in_utf16_or_with_bom_is_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            bom = os.path.join(tmp, "bom.txt")
            with open(bom, "w", encoding="utf-8-sig") as f:
                f.write("Typo.")
            utf16 = os.path.join(tmp, "u16.txt")
            with open(utf16, "w", encoding="utf-16") as f:
                f.write("Typo.")
            server = Server((200, answers(sure_kind("nit"), 0.02, 0.01)))
            code, out = self.run_main(["check_comment", "--comment-file", bom], server)
            self.assertEqual(server.body()["state"]["comment"], "Typo.")
            code16, out16 = self.run_main(["check_comment", "--comment-file", utf16], server)
        self.assertEqual((code, code16), (0, 0))
        self.assertTrue(out.startswith("STATUS: OK"))
        self.assertTrue(out16.startswith("STATUS:"))

    def test_any_transport_failure_still_prints_a_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "c.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("x")
            for failure in (RuntimeError("boom"), httpx2.ReadTimeout("slow"), ValueError("bad")):
                code, out = self.run_main(["check_comment", "--comment-file", path], Server(failure))
                self.assertEqual(code, 0)
                self.assertTrue(out.startswith("STATUS: OK"), failure)
                code, out = self.run_main(["health"], Server(failure))
                self.assertEqual(code, 0)
                self.assertIn("  available: no", out.splitlines())

    def test_health_block(self):
        server = Server((200, {"version": "0.35.0"}), (200, tags("tev1:latest")))
        code, out = self.run_main(["health", "--model", "tev1"], server)
        self.assertEqual(code, 0)
        self.assertIn("  available: yes", out.splitlines())

    def test_model_falls_back_to_the_sdk_env_var(self):
        server = Server((200, {"version": "0.35.0"}), (200, tags("other:latest")))
        os.environ["TYPESAFE_DEFAULT_MODEL"] = "other"
        try:
            _, out = self.run_main(["health"], server)
        finally:
            del os.environ["TYPESAFE_DEFAULT_MODEL"]
        self.assertIn("  model: other", out.splitlines())
        self.assertIn("  available: yes", out.splitlines())


if __name__ == "__main__":
    unittest.main()
