import pytest
from pydantic import ValidationError

from app.schemas import AdCopyStructuredOutput


def test_copy_schema_accepts_valid_structured_output():
    output = AdCopyStructuredOutput(
        title="Move smarter every day",
        marketing_copy="Track workouts, sleep, and energy with one lightweight watch.",
        selling_point_list=["Long battery life", "Sleep insights", "Heart-rate tracking"],
        voiceover_script="Start your morning with a watch that keeps pace with you.",
    )

    assert output.title == "Move smarter every day"
    assert len(output.selling_point_list) == 3


def test_copy_schema_rejects_empty_selling_point_list():
    with pytest.raises(ValidationError):
        AdCopyStructuredOutput(
            title="Move smarter every day",
            marketing_copy="Track workouts, sleep, and energy with one lightweight watch.",
            selling_point_list=[],
            voiceover_script="Start your morning with a watch that keeps pace with you.",
        )


def test_copy_schema_rejects_empty_title():
    with pytest.raises(ValidationError):
        AdCopyStructuredOutput(
            title="",
            marketing_copy="Track workouts, sleep, and energy with one lightweight watch.",
            selling_point_list=["Long battery life"],
            voiceover_script="Start your morning with a watch that keeps pace with you.",
        )
