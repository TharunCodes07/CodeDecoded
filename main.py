import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from state import State
from generate_abstractions.abstractions_generator import generate_chunks, get_file_contents, generate_abstractions
from generate_chapters.generate_chapters import generate_chapters

load_dotenv()

graph = StateGraph(State)
graph.add_node("generate_chunks", generate_chunks)
graph.add_node("get_file_contents", get_file_contents)
graph.add_node("generate_abstractions", generate_abstractions)
graph.add_node("generate_chapters", generate_chapters)

graph.add_edge(START, "generate_chunks")
graph.add_edge("generate_chunks", "get_file_contents")
graph.add_edge("get_file_contents", "generate_abstractions")
graph.add_edge("generate_abstractions", "generate_chapters")
graph.add_edge("generate_chapters", END)

workflow = graph.compile()

def run_workflow(token: str = None, repo: str = None):
    if token is None:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GitHub token not provided. Please set GITHUB_TOKEN environment variable or pass it as a parameter.")
    
    if repo is None:
        repo = os.getenv("GITHUB_REPO")
        if not repo:
            raise ValueError("GitHub repo not provided. Please set GITHUB_REPO environment variable or pass it as a parameter.")
    
    initial_state = {
        "token": token,
        "repo": repo,
    }
    
    result = workflow.invoke(initial_state)
    return result

if __name__ == "__main__":
    out = run_workflow(repo="TharunCodes07/devlabs-backend")