from typing_extensions import Annotated, TypedDict, Optional
from operator import add


class State(TypedDict):
    project_name: Optional[str]
    token: str
    repo: str
    file_contents: Optional[dict]
    chunks: Optional[dict]
    abstractions: Optional[dict]
    summary: Optional[dict]
