import json

import flask_service.chat as chat


def test_chat_uses_local_fallback_without_openai_key(monkeypatch):
    monkeypatch.setattr(chat, "OPENAI_API_KEY", "")
    monkeypatch.setattr(
        chat,
        "_context",
        lambda _username, _recommendations: {"today_progress": {"calories": {"total": 150}}},
    )

    payload, status = chat.chat_with_model(
        "test-user",
        "Which one has more protein?",
        recommendations=[
            {
                "meal": "Greek Yogurt Protein Bowl",
                "nutrients": {"protein": {"amount": 34}, "calories": {"amount": 410}},
                "ingredients": [{"name": "Greek yogurt"}],
            }
        ],
    )

    assert status == 200
    assert payload["success"] is True
    assert payload["data"]["model"] == "local-fallback"
    assert "Greek Yogurt Protein Bowl" in payload["data"]["reply"]


def test_chat_sends_context_to_openai_responses_api(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _traceback):
            return False

        def read(self):
            return json.dumps(
                {"id": "resp_test", "output_text": "Try the Greek yogurt bowl."}
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = dict(request.header_items())
        return FakeResponse()

    monkeypatch.setattr(chat, "OPENAI_API_KEY", "test-key")
    monkeypatch.setattr(chat, "OPENAI_MODEL", "gpt-test")
    monkeypatch.setattr(
        chat,
        "_context",
        lambda username, recommendations: {
            "username": username,
            "today_progress": {"protein": {"total": 20}},
            "current_recommendations": recommendations,
        },
    )
    monkeypatch.setattr(chat.urllib.request, "urlopen", fake_urlopen)

    payload, status = chat.chat_with_model(
        "test-user",
        "What should I pick?",
        history=[{"role": "assistant", "text": "Here are three options."}],
        recommendations=[{"meal": "Greek Yogurt Protein Bowl"}],
    )

    assert status == 200
    assert payload["data"]["reply"] == "Try the Greek yogurt bowl."
    assert payload["data"]["response_id"] == "resp_test"
    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["timeout"] == 30
    assert captured["body"]["model"] == "gpt-test"
    assert captured["body"]["store"] is False
    assert captured["body"]["truncation"] == "auto"
    assert captured["body"]["input"][-1]["content"] == "What should I pick?"
    assert captured["headers"]["Authorization"] == "Bearer test-key"
