import flask_service.chat as chat


def test_chat_uses_local_fallback_without_gemini_key(monkeypatch):
    monkeypatch.setattr(chat, "GEMINI_API_KEY", "")
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


def test_chat_sends_context_to_gemini_generate_content(monkeypatch):
    captured = {}

    def fake_generate_text(system_instruction, messages, temperature, max_tokens):
        captured["system_instruction"] = system_instruction
        captured["messages"] = messages
        captured["temperature"] = temperature
        captured["max_tokens"] = max_tokens
        return "Try the Greek yogurt bowl.", {"responseId": "resp_test"}

    monkeypatch.setattr(chat, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(chat, "GEMINI_MODEL", "gemini-test")
    monkeypatch.setattr(
        chat,
        "_context",
        lambda username, recommendations: {
            "username": username,
            "today_progress": {"protein": {"total": 20}},
            "current_recommendations": recommendations,
        },
    )
    monkeypatch.setattr(chat, "generate_text", fake_generate_text)

    payload, status = chat.chat_with_model(
        "test-user",
        "What should I pick?",
        history=[{"role": "assistant", "text": "Here are three options."}],
        recommendations=[{"meal": "Greek Yogurt Protein Bowl"}],
    )

    assert status == 200
    assert payload["data"]["reply"] == "Try the Greek yogurt bowl."
    assert payload["data"]["response_id"] == "resp_test"
    assert "meal planning assistant" in captured["system_instruction"]
    assert "CURRENT_CONTEXT JSON" in captured["messages"][0][1]
    assert captured["messages"][-1] == ("user", "What should I pick?")
    assert captured["max_tokens"] == 900
