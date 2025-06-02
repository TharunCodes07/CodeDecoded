import json
from langchain_core.prompts import PromptTemplate
from LLM import model
from .tools.tools import get_repository_info, sanitize_json_response, fetch_file_contents, get_unique_file_paths, map_chunks_to_files, count_tokens_per_chunk, create_context_and_file_listing
from prompts import generate_chunks_prompt, json_fixing_prompt, abstractions_json_fixing_prompt, generate_abstractions_prompt, combine_abstractions_prompt
from state import State


def generate_chunks(state: State) -> dict:
    repo_structure, project_name = get_repository_info(state['token'], state['repo'])
    prompt_template = PromptTemplate.from_template(generate_chunks_prompt)
    formatted_prompt = prompt_template.format(structure=repo_structure)
    response = model.generate_content(formatted_prompt).text
    
    sanitized_response = sanitize_json_response(response)
    
    try:
        response_json = json.loads(sanitized_response)
    except json.JSONDecodeError:
        json_fix_template = PromptTemplate.from_template(json_fixing_prompt)
        max_retries = 3
        current_try = 0
        while current_try < max_retries:
            current_try += 1
            formatted_fix_prompt = json_fix_template.format(response_text=sanitized_response)
            response = model.generate_content(formatted_fix_prompt).text
            sanitized_response = sanitize_json_response(response)
            try:
                response_json = json.loads(sanitized_response)
                break
            except json.JSONDecodeError:
                continue
        else:
            raise ValueError("Failed to parse JSON after multiple attempts.")
    return {"chunks": response_json, "project_name": project_name}

def get_file_contents(state: State) -> dict:
    file_paths = get_unique_file_paths(state['chunks'])
    file_contents = fetch_file_contents(state['token'], state['repo'], file_paths)
    return {"file_contents": file_contents}

def generate_abstractions(state: State) -> dict: 
    file_contents = state['file_contents']
    chunks = state['chunks']
    project_name = state['project_name']
    chunks_with_contents = map_chunks_to_files(chunks, file_contents)
    chunk_token_counts = count_tokens_per_chunk(chunks_with_contents)
    if(chunk_token_counts["total"] < 100000):
        context, file_listing = create_context_and_file_listing(chunks_with_contents)
        prompt_template = PromptTemplate.from_template(generate_abstractions_prompt)
        formatted_prompt = prompt_template.format(
            project_name=project_name,
            context=context,
            file_listing=file_listing
        )
        response = model.generate_content(formatted_prompt).text
        sanitized_response = sanitize_json_response(response)
        try:
            abstractions = json.loads(sanitized_response)
        except json.JSONDecodeError:
            json_fix_template = PromptTemplate.from_template(abstractions_json_fixing_prompt)
            max_retries = 3
            current_try = 0
            while current_try < max_retries:
                current_try += 1
                formatted_fix_prompt = json_fix_template.format(response_text=sanitized_response)
                response = model.generate_content(formatted_fix_prompt).text
                sanitized_response = sanitize_json_response(response)
                try:
                    abstractions = json.loads(sanitized_response)
                    break
               
                except json.JSONDecodeError:
                    continue
            else:
                raise ValueError("Failed to parse JSON after multiple attempts.")
    else:
        chunk_abstractions = []
        prompt_template = PromptTemplate.from_template(generate_abstractions_prompt)
        
        for chunk_name, chunk_files in chunks_with_contents.items():
            chunk_context_parts = []
            chunk_file_paths = []
            
            for file_path, content in chunk_files.items():
                chunk_context_parts.append(f"=== {file_path} ===\n{content}\n")
                chunk_file_paths.append(file_path)
            
            chunk_context = "\n".join(chunk_context_parts)
            chunk_file_listing = "\n".join([f"- {file_path}" for file_path in chunk_file_paths])
            
            if not chunk_file_paths:
                continue
                
            formatted_prompt = prompt_template.format(
                project_name=f"{project_name} - {chunk_name}",
                context=chunk_context,
                file_listing=chunk_file_listing
            )
            response = model.generate_content(formatted_prompt).text
            sanitized_response = sanitize_json_response(response)
            
            try:
                chunk_json = json.loads(sanitized_response)
                chunk_abstractions.extend(chunk_json)
            except json.JSONDecodeError:
                json_fix_template = PromptTemplate.from_template(abstractions_json_fixing_prompt)
                max_retries = 3
                current_try = 0
                
                while current_try < max_retries:
                    current_try += 1
                    formatted_fix_prompt = json_fix_template.format(response_text=sanitized_response)
                    response = model.generate_content(formatted_fix_prompt).text
                    sanitized_response = sanitize_json_response(response)
                    try:
                        chunk_json = json.loads(sanitized_response)
                        chunk_abstractions.extend(chunk_json)
                        break
                    except json.JSONDecodeError:
                        continue
        if not chunk_abstractions:
            raise ValueError("Failed to generate any valid abstractions from chunks.")
        chunk_abstractions_json = json.dumps(chunk_abstractions, indent=2)
        combine_template = PromptTemplate.from_template(combine_abstractions_prompt)
        combine_prompt = combine_template.format(
            project_name=project_name,
            chunk_abstractions=chunk_abstractions_json
        )
        
        response = model.generate_content(combine_prompt).text
        sanitized_response = sanitize_json_response(response)
        try:
            abstractions = json.loads(sanitized_response)
        except json.JSONDecodeError:
            json_fix_template = PromptTemplate.from_template(abstractions_json_fixing_prompt)
            max_retries = 3
            current_try = 0
            while current_try < max_retries:
                current_try += 1
                formatted_fix_prompt = json_fix_template.format(response_text=sanitized_response)
                response = model.generate_content(formatted_fix_prompt).text
                sanitized_response = sanitize_json_response(response)
                try:
                    abstractions = json.loads(sanitized_response)
                    break
                except json.JSONDecodeError:
                    continue
            else:
                raise ValueError("Failed to parse combined abstractions JSON after multiple attempts.")
    return {"abstractions": abstractions}
