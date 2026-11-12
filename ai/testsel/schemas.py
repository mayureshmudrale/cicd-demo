from pydantic import BaseModel


class TestSelection(BaseModel):
    __test__ = False  # not a pytest test class, despite the name

    selected_tests: list[str]
    reasoning: str
