from app.services.refinement.refinement_service import refine_transcript


class FakeClient:
    def __init__(self, response):
        self.response = response
        self.model = None
        self.prompt = None

    def generate(self, model, prompt, json_mode=False):
        self.model = model
        self.prompt = prompt
        return self.response


def test_refinement_uses_separate_prompt_and_returns_transcript(monkeypatch):
    monkeypatch.setenv("REFINEMENT_MODEL", "refinement-test-model")
    client = FakeClient("We will not ship Friday.")
    result = refine_transcript("We will not ship Friday.", client=client)
    assert result == "We will not ship Friday."
    assert client.model == "refinement-test-model"
    assert "Do not summarize" in client.prompt
    assert "Preserve exactly" in client.prompt


def test_refinement_rejects_empty_transcript():
    import pytest

    with pytest.raises(ValueError, match="empty transcript"):
        refine_transcript("  ", client=FakeClient("unused"))


def test_refinement_keeps_negation_intact():
    client = FakeClient("Don't deploy the current version.")
    result = refine_transcript(
        "Don't deploy the current version.", client=client)
    assert result == "Don't deploy the current version."
    assert "Don't" in result
