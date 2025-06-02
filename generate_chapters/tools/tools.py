import os
import re

def map_content_to_abstractions(file_contents: dict, abstractions: list) -> dict:
    abstraction_content_map = {}
    
    for abstraction in abstractions:
        abstraction_name = abstraction['name']
        file_paths = abstraction['file_paths']
        combined_content_parts = []
        file_counter = 1
        
        for file_path in file_paths:
            if file_path in file_contents:
                file_content = file_contents[file_path]
                formatted_file = f"--- File: {file_counter} # {file_path} ---\n{file_content}\n"
                combined_content_parts.append(formatted_file)
                file_counter += 1
        
        abstraction_content_map[abstraction_name] = "\n".join(combined_content_parts)
    
    return abstraction_content_map

def check_content_completeness(content: str, chapter_name: str) -> tuple[bool, str]:
    if not content:
        return False, f"Chapter '{chapter_name}' has empty content"
    
    incomplete_indicators = [
        content.strip().endswith((',', 'and', 'or', 'but', 'the', 'a', 'an', 'of', 'in', 'to', 'for')),
        content.count('```') % 2 != 0,
        content.strip().endswith(('-', '*', '+')),
        len(content.strip()) < 500,
        not any(ending in content.lower() for ending in ['conclusion', 'summary', 'next chapter', 'in the next', 'we learned', 'we covered'])
    ]
    
    warning_messages = []
    
    if content.count('```') % 2 != 0:
        warning_messages.append("Unmatched code block markers detected")
    
    if len(content.strip()) < 500:
        warning_messages.append(f"Content is unusually short ({len(content)} characters)")
    
    if content.strip().endswith(('and', 'or', 'but', 'the', 'a', 'an', 'of', 'in', 'to', 'for', ',')):
        warning_messages.append("Content appears to end mid-sentence")
    
    is_complete = not any(incomplete_indicators)
    warning_message = "; ".join(warning_messages) if warning_messages else ""
    
    return is_complete, warning_message


def sanitize_markdown_content(content: str) -> str:
    if not content:
        return ""
    
    content = content.strip()
    
    markdown_pattern = r'^```(?:markdown)?\s*\n(.*?)\n```$'
    match = re.match(markdown_pattern, content, re.DOTALL)
    
    if match:
        content = match.group(1).strip()
    
    if content.startswith('```') and content.endswith('```'):
        lines = content.split('\n')
        if len(lines) > 2:
            if lines[0].strip().startswith('```'):
                lines = lines[1:]
            if lines[-1].strip() == '```':
                lines = lines[:-1]
            content = '\n'.join(lines)
    
    content = re.sub(r'^`{1,3}\s*', '', content)
    content = re.sub(r'\s*`{1,3}$', '', content)
    
    return content.strip()

def create_safe_filename(chapter_name: str, chapter_num: int) -> str:
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', chapter_name)
    safe_name = re.sub(r'\s+', '_', safe_name)
    safe_name = safe_name.strip('_')
    return f"chapter_{chapter_num:02d}_{safe_name}.md"

def ensure_output_directory(base_path: str = None) -> str:
    if base_path is None:
        current_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        base_path = current_dir
    output_dir = os.path.join(base_path, "out")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    return output_dir

def save_chapter_to_file(chapter_content: str, chapter_name: str, chapter_num: int, output_dir: str = None) -> str:
    if output_dir is None:
        output_dir = ensure_output_directory()
    
    sanitized_content = sanitize_markdown_content(chapter_content)
    
    filename = create_safe_filename(chapter_name, chapter_num)
    file_path = os.path.join(output_dir, filename)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(sanitized_content)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            saved_content = f.read()
            
        return file_path
        
    except Exception as e:
        raise

def sanitize_chapter_json_response(response_text: str) -> str:
    if not response_text:
        return ""
    
    response_text = response_text.strip()
    
    start_idx = response_text.find('{')
    if start_idx == -1:
        return response_text
    
    brace_count = 0
    end_idx = -1
    
    for i in range(start_idx, len(response_text)):
        if response_text[i] == '{':
            brace_count += 1
        elif response_text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end_idx = i
                break
    
    if end_idx == -1:
        return response_text
    
    json_content = response_text[start_idx:end_idx + 1]
    
    if '"markdown_content"' in json_content and '"summary"' in json_content:
        return json_content
    
    json_block_pattern = r'```json\s*([\s\S]*?)```'
    json_matches = re.findall(json_block_pattern, response_text)
    
    if json_matches:
        return json_matches[0].strip()
    
    general_block_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    general_matches = re.findall(general_block_pattern, response_text)
    
    if general_matches:
        for match in general_matches:
            if '"markdown_content"' in match and '"summary"' in match:
                return match.strip()
    
    return json_content