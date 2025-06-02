import requests
import json
import re
import base64
import concurrent.futures
import tiktoken


def format_repository_structure(tree_data):
    structure_lines = []
    for item in tree_data['tree']:
        path = item['path']
        depth = path.count('/')
        indent = "  " * depth
        name = path.split('/')[-1]
        
        if item['type'] == 'tree':
            structure_lines.append(f"{indent}{name}/")
        else:
            structure_lines.append(f"{indent}{name}")
    
    return "\n".join(structure_lines)


def get_repository_info(token: str, repo: str) -> dict:
    repo_url = f"https://api.github.com/repos/{repo}"
    headers = {"Authorization": f"token {token}"}
    repo_response = requests.get(repo_url, headers=headers)
    repo_response.raise_for_status()
    repo_data = repo_response.json()
    default_branch = repo_data['default_branch']
    project_name = repo_data['name']
    
    tree_url = f"https://api.github.com/repos/{repo}/git/trees/{default_branch}?recursive=1"
    response = requests.get(tree_url, headers=headers)
    response.raise_for_status()
    tree_data = response.json()
    
    structure = format_repository_structure(tree_data)
    return structure, project_name

def fetch_file_contents(token: str, repo: str, file_paths: list) -> dict:
    file_contents = {}
    headers = {"Authorization": f"token {token}"}
    
    def fetch_single_file(file_path):
        """Helper function to fetch a single file's content"""
        file_url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
        response = requests.get(file_url, headers=headers)
        
        if response.status_code == 200:
            file_data = response.json()
            if 'content' in file_data:
                try:
                    content = base64.b64decode(file_data['content']).decode('utf-8')
                    return file_path, content
                except Exception as e:
                    print(f"Error decoding content for {file_path}: {e}")
        
        return file_path, None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_file = {executor.submit(fetch_single_file, file_path): file_path 
                          for file_path in file_paths if file_path not in file_contents}
        for future in concurrent.futures.as_completed(future_to_file):
            file_path, content = future.result()
            if content is not None:
                file_contents[file_path] = content
    return file_contents

def sanitize_json_response(response_text: str) -> str:
    response_text = response_text.strip()
    json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(json_pattern, response_text)
    
    if matches:
        response_text = matches[0].strip()
    elif response_text.startswith('{') and response_text.endswith('}'):
        pass
    else:
        json_content_pattern = r'({[\s\S]*?})'
        content_matches = re.findall(json_content_pattern, response_text)
        if content_matches:
            response_text = content_matches[0].strip()
    
    return response_text

def get_unique_file_paths(chunks):
    file_paths = []
    for chunk_files in chunks.values():
        file_paths.extend(chunk_files)
    return list(set(file_paths))

def map_chunks_to_files(chunks, file_contents):
    result = {}
    for chunk_name, file_paths in chunks.items():
        chunk_files = {}
        for file_path in file_paths:
            if file_path in file_contents:
                chunk_files[file_path] = file_contents[file_path]
        result[chunk_name] = chunk_files
    return result

def count_tokens(text: str) -> int:
    return len(text) // 4

def count_tokens_per_chunk(chunks_with_contents: dict) -> dict:
    result = {
        "total": 0,
        "per_chunk": {}
    }
    
    for chunk_name, files in chunks_with_contents.items():
        file_tokens = {path: count_tokens(content) for path, content in files.items()}
        chunk_total = sum(file_tokens.values())
        result["per_chunk"][chunk_name] = {
            "total": chunk_total,
            "per_file": file_tokens
        }
        result["total"] += chunk_total
    return result

def create_context_and_file_listing(chunks_with_contents: dict) -> tuple[str, str]:
    context_parts = []
    all_files = []
    
    for files in chunks_with_contents.values():
        for file_path, content in files.items():
            context_parts.append(f"=== {file_path} ===\n{content}\n")
            all_files.append(file_path)
    
    context = "\n".join(context_parts)
    file_listing = "\n".join([f"- {file_path}" for file_path in all_files])
    
    return context, file_listing


