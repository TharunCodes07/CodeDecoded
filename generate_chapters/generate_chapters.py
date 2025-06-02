import json
from langchain_core.prompts import PromptTemplate
from LLM import model
from .tools.tools import map_content_to_abstractions, save_chapter_to_file, ensure_output_directory, sanitize_chapter_json_response, check_content_completeness
from prompts import create_chapters_prompt, chapter_json_fixing_prompt
from state import State


def generate_chapters(state: State) -> dict:
    chapters = {}
    summaries = []
    chapter_files = map_content_to_abstractions(state['file_contents'], state['abstractions'])
    output_dir = ensure_output_directory()
    
    complete_tutorial_structure = ""
    for i, abstraction in enumerate(state['abstractions'], 1):
        complete_tutorial_structure += f"Chapter {i}: {abstraction['name']}\n"
    
    project_name = state.get('project_name', 'Unknown Project')
    
    for i, abstraction in enumerate(state['abstractions']):
        chapter_name = abstraction['name']
        chapter_desc = abstraction['description']
        chapter_content = chapter_files.get(chapter_name, "")
        chapter_num = i + 1
        
        if i == 0:
            previous_chapters_summary = "This is the first chapter"
        else:
            previous_chapters_summary = " ".join(summaries)
        
        prompt_template = PromptTemplate.from_template(create_chapters_prompt)
        formatted_prompt = prompt_template.format(
            project_name=project_name,
            abstraction_name=chapter_name,
            chapter_num=chapter_num,
            abstraction_description=chapter_desc,
            complete_tutorial_structure=complete_tutorial_structure,
            previous_chapters_summary=previous_chapters_summary,
            file_context_str=chapter_content
        )
        
        try:
            response = model.generate_content(formatted_prompt).text
            sanitized_response = sanitize_chapter_json_response(response)
            
            chapter_json = None
            parsing_attempts = 0
            
            try:
                parsing_attempts += 1
                chapter_json = json.loads(sanitized_response)
                
            except json.JSONDecodeError as e:
                json_fix_template = PromptTemplate.from_template(chapter_json_fixing_prompt)
                max_retries = 3
                current_try = 0
                while current_try < max_retries:
                    current_try += 1
                    parsing_attempts += 1
                    
                    formatted_fix_prompt = json_fix_template.format(response_text=sanitized_response)
                    
                    try:
                        response = model.generate_content(formatted_fix_prompt).text
                        sanitized_response = sanitize_chapter_json_response(response)
                        chapter_json = json.loads(sanitized_response)
                        break
                        
                    except json.JSONDecodeError as fix_error:
                        continue
                        
                if chapter_json is None:
                    error_msg = f"Failed to parse chapter JSON for {chapter_name} after {parsing_attempts} attempts."
                    raise ValueError(error_msg)
            
            if 'markdown_content' not in chapter_json:
                raise ValueError(f"Missing 'markdown_content' in chapter JSON for {chapter_name}")
                
            if 'summary' not in chapter_json:
                raise ValueError(f"Missing 'summary' in chapter JSON for {chapter_name}")
            
            markdown_content = chapter_json['markdown_content']
            summary = chapter_json['summary']
            is_complete, warning_msg = check_content_completeness(markdown_content, chapter_name)
            if not is_complete:
                if len(markdown_content.strip()) < 200:
                    raise ValueError(f"Generated content for {chapter_name} is too short: {len(markdown_content)} characters")
            
            try:
                saved_file_path = save_chapter_to_file(markdown_content, chapter_name, chapter_num, output_dir)
                
                with open(saved_file_path, 'r', encoding='utf-8') as f:
                    saved_content = f.read()
                    
            except Exception as save_error:
                raise save_error

            chapters[chapter_name] = markdown_content
            summaries.append(summary)
            
        except Exception as chapter_error:
            raise
    
    return {"summary": summaries}

