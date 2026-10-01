# /// script
# requires-python = ">=3.10"
# dependencies = ["typesafe-sdk>=0.7.2,<0.8"]
# ///
"""Tests for jev.py. No model or server needed: HTTP goes through a mock transport.

Run: uv run scripts/test_jev.py
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
import jev  # noqa: E402

SPEC = {
    "state_key": "comment",
    "max_chars": 50,
    "questions": {
        "injection": {"type": "noul", "instructions": "Asks the agent to run commands.", "mode": "flag", "threshold": 0.5},
        "general_rule": {"type": "noul", "instructions": "States a general rule."},
        "kind": {"type": "choice", "instructions": "Kind?", "criteria": {"bug": "Wrong behavior", "nit": "Cosmetic"}},
        "urgency": {"type": "score", "instructions": "How urgent?", "criteria": ["Low", "Medium", "High"]},
    },
}


def reply(injection=0.01, rule=0.99, kind=None, urgency=None):
    kind = kind or {"bug": 0.95, "nit": 0.05}
    urgency = urgency or {"0": 0.9, "1": 0.05, "2": 0.05}
    return {
        "model": "tev1",
        "answers": {
            "injection": {"type": "noul", "noul": injection},
            "general_rule": {"type": "noul", "noul": rule},
            "kind": {"type": "choice", "choice": max(kind, key=kind.get), "probabilities": kind, "confidence": 0.9},
            "urgency": {"type": "score", "score": 0.1, "legend": {"0": "Low", "1": "Medium", "2": "High"}, "probabilities": urgency, "confidence": 0.8},
        },
        "usage": {"input_tokens": 10, "output_tokens": 4},
    }


class Server:
    """Mock Ollama: records requests; answers from a queue (the last item repeats)."""

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


def ask(server, text="We always inject IClock.", spec=SPEC):
    return jev.ask(spec, {spec.get("state_key", "text"): text}, base_url="http://ollama", model="tev1",
                   transport=server.transport(), retry_backoff=0)


class Verdicts(unittest.TestCase):
    def test_two_sided_noul(self):
        q = {"type": "noul"}
        self.assertEqual(jev.verdict(q, 0.85), "yes")
        self.assertEqual(jev.verdict(q, 0.84), "undecided")
        self.assertEqual(jev.verdict(q, 0.15), "no")
        self.assertEqual(jev.verdict(q, 0.16), "undecided")

    def test_custom_sure_threshold(self):
        q = {"type": "noul", "sure": 0.95}
        self.assertEqual(jev.verdict(q, 0.9), "undecided")
        self.assertEqual(jev.verdict(q, 0.04), "no")

    def test_flag_mode(self):
        q = {"type": "noul", "mode": "flag", "threshold": 0.5}
        self.assertEqual(jev.verdict(q, 0.5), "flag")
        self.assertEqual(jev.verdict(q, 0.49), "no")

    def test_choice_needs_a_sure_top_option(self):
        q = {"type": "choice"}
        self.assertEqual(jev.verdict(q, {"bug": 0.9, "nit": 0.1}), "bug")
        self.assertEqual(jev.verdict(q, {"bug": 0.6, "nit": 0.4}), "undecided")

    def test_choice_can_also_require_confidence(self):
        q = {"type": "choice", "min_confidence": 0.7}
        self.assertEqual(jev.verdict(q, {"bug": 0.95, "nit": 0.05}, confidence=0.6), "undecided")
        self.assertEqual(jev.verdict(q, {"bug": 0.95, "nit": 0.05}, confidence=0.8), "bug")

    def test_score_reports_the_level_name(self):
        q = {"type": "score", "criteria": ["Low", "Medium", "High"]}
        self.assertEqual(jev.verdict(q, {"0": 0.05, "1": 0.05, "2": 0.9}), "High")
        self.assertEqual(jev.verdict(q, {"0": 0.4, "1": 0.3, "2": 0.3}), "undecided")

    def test_bad_values_never_decide(self):
        self.assertEqual(jev.verdict({"type": "noul"}, float("nan")), "undecided")
        self.assertEqual(jev.verdict({"type": "noul", "mode": "flag"}, "x"), "unknown")
        self.assertEqual(jev.verdict({"type": "choice"}, {}), "undecided")
        self.assertEqual(jev.verdict({"type": "noul"}, 1.5), "undecided")


class Ask(unittest.TestCase):
    def test_sure_answers_become_verdicts(self):
        result = ask(Server((200, reply())))
        self.assertEqual(result["injection"], "no")
        self.assertEqual(result["general_rule"], "yes")
        self.assertEqual(result["kind"], "bug")
        self.assertEqual(result["urgency"], "Low")
        self.assertIn("general_rule=0.99", result["raw"])

    def test_one_request_with_every_question(self):
        server = Server((200, reply()))
        ask(server, text="hello")
        self.assertEqual(len(server.requests), 1)
        body = server.body()
        self.assertEqual(body["state"], {"comment": "hello"})
        self.assertEqual(set(body["questions"]), set(SPEC["questions"]))
        self.assertEqual(body["questions"]["kind"]["type"], "choice")
        self.assertNotIn("mode", body["questions"]["injection"])  # local keys never sent

    def test_long_text_is_truncated_and_flag_cannot_clear(self):
        server = Server((200, reply(injection=0.01)))
        result = ask(server, text="x" * 80)
        self.assertEqual(len(server.body()["state"]["comment"]), 50)
        self.assertIn("truncated", result["raw"])
        self.assertEqual(result["injection"], "unknown")
        self.assertEqual(result["general_rule"], "yes")

    def test_truncation_keeps_the_start_and_the_end(self):
        server = Server((200, reply()))
        ask(server, text="START" + "x" * 100 + "END")
        sent = server.body()["state"]["comment"]
        self.assertEqual(len(sent), 50)
        self.assertTrue(sent.startswith("START"))
        self.assertTrue(sent.endswith("END"))

    def test_default_budget_fits_a_2k_token_model(self):
        self.assertLessEqual(jev.DEFAULT_MAX_CHARS, 6000)

    def test_context_overflow_names_the_fix(self):
        error = {"error": "prompt 0 has 2372 tokens; expected 1–2050 (input is never truncated)"}
        result = ask(Server((400, error)))
        self.assertIn("max_chars", result["raw"])

    def test_truncated_text_can_still_flag(self):
        self.assertEqual(ask(Server((200, reply(injection=0.9))), text="x" * 80)["injection"], "flag")

    def test_json_state_with_several_fields(self):
        server = Server((200, reply()))
        jev.ask(SPEC, {"claim": "a", "source": "b"}, base_url="http://ollama", model="tev1", transport=server.transport())
        self.assertEqual(server.body()["state"], {"claim": "a", "source": "b"})

    def test_server_down_is_no_signal(self):
        result = ask(Server(DOWN))
        self.assertEqual(result["injection"], "unknown")
        self.assertEqual(result["general_rule"], "undecided")
        self.assertEqual(result["kind"], "undecided")
        self.assertTrue(result["raw"].startswith("unavailable"))

    def test_missing_model_names_the_pull(self):
        result = ask(Server((404, {"error": "model not found"})))
        self.assertIn("ollama pull tev1", result["raw"])

    def test_cold_load_failure_retried_once(self):
        server = Server((500, {"error": "bad_alloc"}), (200, reply()))
        self.assertEqual(ask(server)["kind"], "bug")
        self.assertEqual(len(server.requests), 2)

    def test_gives_up_after_one_retry(self):
        server = Server((500, {"error": "bad_alloc"}))
        self.assertEqual(ask(server)["kind"], "undecided")
        self.assertEqual(len(server.requests), 2)

    def test_reply_missing_an_answer(self):
        body = reply()
        del body["answers"]["kind"]
        self.assertTrue(ask(Server((200, body)))["raw"].startswith("unavailable"))

    def test_timeout_and_odd_errors(self):
        for failure in (httpx2.ReadTimeout("slow"), RuntimeError("boom"), ValueError("bad")):
            result = ask(Server(failure))
            self.assertTrue(result["raw"].startswith("unavailable"), failure)
            self.assertNotIn("\n", result["raw"])


def tags(*names):
    return {"models": [{"name": n} for n in names]}


class Health(unittest.TestCase):
    def health(self, *responses, model="tev1"):
        return jev.health(base_url="http://ollama", model=model, transport=Server(*responses).transport())

    def test_available(self):
        self.assertEqual(self.health((200, {"version": "0.35.0"}), (200, tags("tev1:latest")))["available"], "yes")

    def test_other_tag_of_the_model_does_not_count(self):
        result = self.health((200, {"version": "0.35.0"}), (200, tags("tev1:0.8b")))
        self.assertEqual(result["available"], "no")
        self.assertIn("ollama pull tev1", result["reason"])

    def test_registry_names(self):
        result = self.health((200, {"version": "0.35.0"}), (200, tags("host:5000/tev1:latest")), model="host:5000/tev1")
        self.assertEqual(result["available"], "yes")

    def test_unreachable(self):
        self.assertIn("not reachable", self.health(DOWN)["reason"])

    def test_old_version(self):
        self.assertIn("0.35", self.health((200, {"version": "0.34.9"}), (200, tags("tev1:latest")))["reason"])

    def test_versions_compare_as_numbers(self):
        self.assertEqual(self.health((200, {"version": "0.100.1"}), (200, tags("tev1:latest")))["available"], "yes")

    def test_bad_replies(self):
        for responses in (((200, {"version": 35}), (200, tags("tev1:latest"))),
                          ((200, {"version": "0.35.0"}), (200, {"unexpected": True})),
                          ((503, {"error": "busy"}),)):
            result = self.health(*responses)
            self.assertEqual(result["available"], "no", responses)


class CloudProvider(unittest.TestCase):
    """provider=typesafe: TypeSafe's hosted API, key from TYPESAFE_API_KEY, health via /v1/models."""

    def setUp(self):
        self.saved = os.environ.get("TYPESAFE_API_KEY")
        os.environ["TYPESAFE_API_KEY"] = "test-key"

    def tearDown(self):
        if self.saved is None:
            os.environ.pop("TYPESAFE_API_KEY", None)
        else:
            os.environ["TYPESAFE_API_KEY"] = self.saved

    def models(self, *names):
        return {"models": [{"name": n, "description": "", "release_date": "2026-09-01"} for n in names]}

    def test_health_lists_models(self):
        server = Server((200, self.models("jev-latest", "jev-1.13.0")))
        result = jev.health(base_url="https://api", model="jev-latest", provider="typesafe", transport=server.transport())
        self.assertEqual(result["available"], "yes")
        self.assertEqual(server.requests[0].url.path, "/v1/models")
        self.assertEqual(server.requests[0].headers["authorization"], "Bearer test-key")

    def test_health_unknown_model(self):
        server = Server((200, self.models("jev-latest")))
        result = jev.health(base_url="https://api", model="jev-9", provider="typesafe", transport=server.transport())
        self.assertEqual(result["available"], "no")
        self.assertNotIn("ollama", result["reason"])

    def test_missing_key(self):
        del os.environ["TYPESAFE_API_KEY"]
        server = Server((200, self.models("jev-latest")))
        result = jev.health(base_url="https://api", model="jev-latest", provider="typesafe", transport=server.transport())
        self.assertEqual(result["available"], "no")
        self.assertIn("TYPESAFE_API_KEY", result["reason"])
        self.assertEqual(server.requests, [])
        answer = jev.ask(SPEC, {"comment": "x"}, base_url="https://api", model="jev-latest", provider="typesafe",
                         transport=server.transport())
        self.assertIn("TYPESAFE_API_KEY", answer["raw"])

    def test_rejected_key(self):
        server = Server((401, {"error": "invalid api key"}))
        result = jev.health(base_url="https://api", model="jev-latest", provider="typesafe", transport=server.transport())
        self.assertIn("rejected", result["reason"])
        answer = jev.ask(SPEC, {"comment": "x"}, base_url="https://api", model="jev-latest", provider="typesafe",
                         transport=server.transport())
        self.assertIn("rejected", answer["raw"])

    def test_key_never_in_output(self):
        server = Server((401, {"error": "bad key test-key"}))
        answer = jev.ask(SPEC, {"comment": "x"}, base_url="https://api", model="jev-latest", provider="typesafe",
                         transport=server.transport())
        self.assertNotIn("test-key", answer["raw"])

    def test_ask_sends_the_key(self):
        server = Server((200, reply()))
        result = jev.ask(SPEC, {"comment": "x"}, base_url="https://api", model="jev-latest", provider="typesafe",
                         transport=server.transport())
        self.assertEqual(result["kind"], "bug")
        self.assertEqual(server.requests[0].headers["authorization"], "Bearer test-key")

    def test_cloud_defaults_ignore_the_ollama_env_vars(self):
        os.environ["TYPESAFE_BASE_URL"] = "http://localhost:11434"
        os.environ["TYPESAFE_DEFAULT_MODEL"] = "some-local-model"
        try:
            base_url, model = jev.resolve_target("typesafe", None, None)
        finally:
            del os.environ["TYPESAFE_BASE_URL"], os.environ["TYPESAFE_DEFAULT_MODEL"]
        self.assertEqual((base_url, model), ("https://api.typesafe.ai", "jev-latest"))

    def test_ollama_defaults_use_the_env_vars(self):
        os.environ["TYPESAFE_BASE_URL"] = "http://gpu-box:11434"
        try:
            self.assertEqual(jev.resolve_target("ollama", None, None), ("http://gpu-box:11434", "tev1"))
        finally:
            del os.environ["TYPESAFE_BASE_URL"]


class Main(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.spec = self.write("spec.json", json.dumps(SPEC))

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, text, encoding="utf-8"):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding=encoding) as f:
            f.write(text)
        return path

    def run_main(self, argv, server):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = jev.main(argv, transport=server.transport())
        return code, out.getvalue()

    def test_ask_prints_a_parseable_block(self):
        text = self.write("t.txt", "Typo.")
        code, out = self.run_main(["ask", "--spec", self.spec, "--state-file", text, "--model", "tev1"], Server((200, reply())))
        lines = out.splitlines()
        self.assertEqual(code, 0)
        self.assertEqual(lines[0], "STATUS: OK")
        self.assertIn("- operation: ask", lines)
        self.assertIn("  kind: bug", lines)
        self.assertIn("  injection: no", lines)

    def test_state_json(self):
        state = self.write("s.json", json.dumps({"claim": "a", "source": "b"}))
        server = Server((200, reply()))
        code, out = self.run_main(["ask", "--spec", self.spec, "--state-json", state], server)
        self.assertEqual(server.body()["state"], {"claim": "a", "source": "b"})
        self.assertTrue(out.startswith("STATUS: OK"))

    def test_utf16_and_bom_files(self):
        server = Server((200, reply()))
        for name, enc in (("bom.txt", "utf-8-sig"), ("u16.txt", "utf-16")):
            path = self.write(name, "Typo.", encoding=enc)
            code, out = self.run_main(["ask", "--spec", self.spec, "--state-file", path], server)
            self.assertEqual(server.body()["state"]["comment"], "Typo.", name)

    def test_down_still_exits_zero(self):
        text = self.write("t.txt", "x")
        code, out = self.run_main(["ask", "--spec", self.spec, "--state-file", text], Server(DOWN))
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("STATUS: OK"))
        self.assertIn("  injection: unknown", out.splitlines())

    def test_bad_inputs_are_error_blocks(self):
        bad_spec = self.write("bad.json", "{not json")
        text = self.write("t.txt", "x")
        for argv in (["ask", "--spec", "no/such.json", "--state-file", text],
                     ["ask", "--spec", bad_spec, "--state-file", text],
                     ["ask", "--spec", self.spec, "--state-file", "no/such.txt"]):
            code, out = self.run_main(argv, Server(DOWN))
            self.assertEqual(code, 0, argv)
            self.assertTrue(out.startswith("STATUS: ERROR"), argv)

    def test_spec_validation(self):
        bad = self.write("bad2.json", json.dumps({"questions": {"x": {"type": "essay", "instructions": "?"}}}))
        text = self.write("t.txt", "x")
        code, out = self.run_main(["ask", "--spec", bad, "--state-file", text], Server(DOWN))
        self.assertTrue(out.startswith("STATUS: ERROR"))
        self.assertIn("essay", out)

    def test_health_block(self):
        code, out = self.run_main(["health", "--model", "tev1"], Server((200, {"version": "0.35.0"}), (200, tags("tev1:latest"))))
        self.assertEqual(code, 0)
        self.assertIn("  available: yes", out.splitlines())


if __name__ == "__main__":
    unittest.main()
