from typing_extensions import TypedDict, Optional


class State(TypedDict):
    project_name: Optional[str]
    token: str
    repo: str
    file_contents: Optional[dict]
    chunks: Optional[dict]
    abstractions: Optional[dict]