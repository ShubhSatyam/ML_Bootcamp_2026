import pytest

from app.services.documentation.documentation_service import _parse_documentation, generate_meeting_documentation


class FakeClient:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.prompts = []

    def generate(self, model, prompt, json_mode=False):
        self.prompts.append(prompt)
        return next(self.responses)


def test_extracts_explicit_task_owner_and_deadline():
    output = _parse_documentation(
        '{"summary":"Report follow-up","minutes":[],"decisions":[],"tasks":'
        '[{"task":"Prepare the report","owner":"Rahul","deadline":"Friday"}]}'
    )
    assert output.tasks[0].owner == "Rahul"
    assert output.tasks[0].deadline == "Friday"


def test_missing_task_owner_and_deadline_become_unspecified():
    output = _parse_documentation(
        '{"summary":"A report was discussed","minutes":[],"decisions":[],"tasks":'
        '[{"task":"Prepare the report"}]}'
    )
    assert output.tasks[0].owner == "Unspecified"
    assert output.tasks[0].deadline == "Unspecified"


def test_proposal_is_not_automatically_a_decision():
    output = _parse_documentation(
        '{"summary":"PostgreSQL was discussed","minutes":["A possible database change was discussed"],'
        '"decisions":[],"tasks":[]}'
    )
    assert output.decisions == []


def test_repairs_trailing_comma():
    output = _parse_documentation(
        '{"summary":"Discussed","minutes":[],"decisions":[],"tasks":[],}')
    assert output.tasks == []


def test_retries_invalid_json_once_then_returns_validated_record():
    client = FakeClient([
        "not json",
        '{"summary":"Discussed","minutes":[],"decisions":[],"tasks":[]}',
    ])
    output = generate_meeting_documentation(
        "We discussed the report.", client=client)
    assert output.summary == "Discussed"
    assert len(client.prompts) == 2
    assert all("We discussed the report." in prompt for prompt in client.prompts)


def test_invalid_json_after_retry_is_controlled_error():
    client = FakeClient(["bad", "still bad"])
    with pytest.raises(RuntimeError, match="after one retry"):
        generate_meeting_documentation("Transcript.", client=client)


def test_explicit_agreement_creates_a_decision():
    output = _parse_documentation(
        '{"summary":"Marketing planning","minutes":[],"decisions":[{"decision":"We will launch on Friday","evidence":"The marketing team agreed that we will launch on Friday."}],"tasks":[]}'
    )
    assert output.decisions[0].decision == "We will launch on Friday"


def test_non_committal_possible_launch_is_not_a_decision():
    output = _parse_documentation(
        '{"summary":"Launch timing discussed","minutes":["Maybe we should launch on Friday."],"decisions":[],"tasks":[]}'
    )
    assert output.decisions == []


def test_explicit_task_includes_owner_and_deadline():
    output = _parse_documentation(
        '{"summary":"Reporting follow-up","minutes":[],"decisions":[],"tasks":[{"task":"Prepare the report","owner":"Rahul","deadline":"Friday"}]}'
    )
    assert output.tasks[0].owner == "Rahul"
    assert output.tasks[0].deadline == "Friday"


def test_vague_task_uses_unspecified_fields():
    output = _parse_documentation(
        '{"summary":"Reporting follow-up","minutes":[],"decisions":[],"tasks":[{"task":"Someone should prepare the report"}]}'
    )
    assert output.tasks[0].owner == "Unspecified"
    assert output.tasks[0].deadline == "Unspecified"


def test_possible_task_request_is_not_a_confirmed_action():
    output = _parse_documentation(
        '{"summary":"Task delegation discussed","minutes":["We could ask Rahul to prepare the report."],"decisions":[],"tasks":[]}'
    )
    assert output.tasks == []


def test_rejects_blank_summary_and_blank_minute_entries():
    with pytest.raises(ValueError, match="schema"):
        _parse_documentation(
            '{"summary":" ","minutes":[""],"decisions":[],"tasks":[]}'
        )
