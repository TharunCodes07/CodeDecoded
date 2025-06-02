generate_chunks_prompt = """Given the following real project file structure, return a JSON that groups only the important and relevant source code files into logical chunks (e.g., "authentication", "core config", "review system", etc.).

Do not include or assume any files or folders not explicitly listed.

Exclude all non-essential files such as:
- Dependency files (e.g., package.json, build.gradle, requirements.txt, pnpm-lock.yaml, etc.)
- Dotfiles and configs (e.g., .env, .gitignore, .gitattributes, README.md, etc.)
- Build tools and wrappers (e.g., gradlew, Makefile, Dockerfile)

Only consider real, relevant source folders like:
- src, app, lib, components, controllers, services, models, routes, pages, etc.

Do not hallucinate any files. Only use what is actually listed below.

Return only a JSON response with no more than 5 top-level chunks, in this exact format:

{{
  "chunkName1": [ "relative/path/to/file1", "relative/path/to/file2" ],
  "chunkName2": [ "relative/path/to/file3" ]
}}

REAL Project Structure:
{structure}
"""



json_fixing_prompt = """You are a JSON fixer.

You will be given a string that is supposed to be a JSON object in the following format:

{{
  "chunkName1": [ "relative/path/to/file1", "relative/path/to/file2" ],
  "chunkName2": [ "relative/path/to/file3" ]
}}

Your task:
1. If the input is valid JSON, return it as-is.
2. If it's invalid (e.g., extra text, explanations, trailing commas, or missing brackets), fix it and return only the corrected JSON object.

Do not include any explanation or text—only return the valid JSON object.

Input:
{response_text}
"""


chapter_json_fixing_prompt = """You are a JSON fixer for chapter generation responses.

You will be given a string that is supposed to be a JSON object in the following format:

{{
  "markdown_content": "The complete markdown content for the chapter goes here...",
  "summary": "A concise 2-3 sentence summary of what this chapter covers, including the main concepts and key takeaways for beginners."
}}

Your task:
1. If the input is valid JSON, return it as-is.
2. If it's invalid (e.g., extra text, explanations, trailing commas, missing brackets, or unescaped quotes in the content), fix it and return only the corrected JSON object.
3. If the JSON appears to be truncated or incomplete, try to complete it by adding closing brackets/braces and quotes where needed.
4. Properly escape any quotes, newlines, and special characters in the markdown_content and summary fields.
5. Ensure the markdown_content contains properly formatted markdown without extra markdown code block wrappers (no ```markdown or ``` at the beginning/end).
6. If the content appears to be cut off mid-sentence, add a note like "... [Content may be truncated]" to indicate incomplete content.
7. Ensure both "markdown_content" and "summary" fields are present and contain valid string values.

Do not include any explanation or text—only return the valid JSON object.

Input:
{response_text}
"""


abstractions_json_fixing_prompt = """You are a JSON fixer for abstractions generation responses.

You will be given a string that is supposed to be a JSON array of objects in the following format:

[
  {{
    "name": "Abstraction Name",
    "description": "A detailed description of what this abstraction does...",
    "file_paths": [
      "path/to/file1.py",
      "path/to/file2.js"
    ]
  }},
  {{
    "name": "Another Abstraction",
    "description": "Another description...",
    "file_paths": [
      "path/to/another.py"
    ]
  }}
]

Your task:
1. If the input is valid JSON, return it as-is.
2. If it's invalid (e.g., extra text, explanations, trailing commas, missing brackets, or unescaped quotes), fix it and return only the corrected JSON array.
3. Properly escape any quotes, newlines, and special characters in the name, description, and file_paths fields.
4. Ensure each object has all required fields: name, description, and file_paths.
5. Make sure file_paths is always an array, even if it contains only one file.

Do not include any explanation or text—only return the valid JSON array.

Input:
{response_text}
"""


generate_abstractions_prompt = """For the project `{project_name}`:

Codebase Context:
{context}

Analyze the codebase context.
Identify the top 3-7 core most important abstractions to help those new to the codebase.

For each abstraction, provide:
1. A concise `name`.
2. A beginner-friendly `description` explaining what it is with a simple analogy, in around 100 words.
3. A list of relevant `file_paths` using the actual file paths.

List of files present in the context:
{file_listing}

Format the output as a JSON array of objects:

```json
[
  {{
    "name": "Query Processing",
    "description": "Explains what the abstraction does. It's like a central dispatcher routing requests.",
    "file_paths": [
      "path/to/file1.py",
      "path/to/related.py"
    ]
  }},
  {{
    "name": "Query Optimization", 
    "description": "Another core concept, similar to a blueprint for objects.",
    "file_paths": [
      "path/to/another.js"
    ]
  }}
]
```
"""

combine_abstractions_prompt = """You are tasked with combining multiple per-chunk abstractions from a codebase into a single, cohesive final abstraction.

Project: {project_name}

Here are the individual abstractions from different chunks:
{chunk_abstractions}

Your task:
1. Analyze all the provided abstractions carefully
2. **Intelligently merge only closely related concepts** - don't force unrelated things together
3. **Preserve distinct, well-defined abstractions** - each should represent a clear, focused concept
4. **Eliminate true redundancy** while keeping important nuances that make concepts unique
5. **Maintain up to 8 high-quality abstractions** - quality over quantity
6. Ensure file paths are correctly preserved and consolidated

Return a JSON array with the final combined abstractions in this exact format:

```json
[
  {{
    "name": "Focused Concept Name",
    "description": "A detailed, well-crafted description that explains this specific abstraction clearly. Focus on what makes this concept unique and important. Aim for 100-150 words with good depth.",
    "file_paths": [
      "all/relevant/file/paths.py",
      "from/different/chunks.js"
    ]
  }}
]
```

**Smart Combination Guidelines:**
- **Only merge abstractions that are truly similar** (e.g., "User Login" + "Authentication Service" = "User Authentication System")
- **Keep distinct concepts separate** (e.g., don't merge "Database Layer" with "API Routes" - they're different concerns)
- **Preserve architectural boundaries** - respect separation of concerns
- **Each abstraction should feel complete and self-contained**
- **Aim for 5-8 well-detailed abstractions** rather than forcing everything into fewer buckets
- **Write rich descriptions** that help newcomers understand both what the abstraction does and why it matters
- **Prioritize core system components, architectural patterns, and key business logic**
"""

create_chapters_prompt = """
Write a very beginner-friendly tutorial chapter (in Markdown format) for the project {project_name} about the concept: "{abstraction_name}". This is Chapter {chapter_num}.

Concept Details:

Name: {abstraction_name}
Description:
{abstraction_description}
Complete Tutorial Structure:
{complete_tutorial_structure}

Context from previous chapters:
{previous_chapters_summary}

Relevant Code Snippets (Code itself remains unchanged):
{file_context_str}

Instructions for the chapter:

Start with a clear heading (e.g., # Chapter {chapter_num} : {abstraction_name}). Use the provided concept name.

If this is not the first chapter, begin with a brief transition from the previous chapter, referencing it with a proper Markdown link using its name.

Begin with a high-level motivation explaining what problem this abstraction solves. Start with a central use case as a concrete example. The whole chapter should guide the reader to understand how to solve this use case. Make it very minimal and friendly to beginners.

If the abstraction is complex, break it down into key concepts. Explain each concept one-by-one in a very beginner-friendly way.

Explain how to use this abstraction to solve the use case. Give example inputs and outputs for code snippets (if the output isn't values, describe at a high level what will happen).

Each code block should be BELOW 10 lines! If longer code blocks are needed, break them down into smaller pieces and walk through them one-by-one. Aggressively simplify the code to make it minimal. Use comments to skip non-important implementation details. Each code block should have a beginner-friendly explanation right after it.

Describe the internal implementation to help understand what's under the hood. First provide a non-code or code-light walkthrough on what happens step-by-step when the abstraction is called. It's recommended to use a simple sequenceDiagram with a dummy example - keep it minimal with at most 5 participants to ensure clarity. If participant name has space, use: participant QP as Query Processing.

Then dive deeper into code for the internal implementation with references to files. Provide example code blocks, but make them similarly simple and beginner-friendly. Explain.

IMPORTANT: When you need to refer to other core abstractions covered in other chapters, ALWAYS use proper Markdown links like this: Chapter Title. Use the Complete Tutorial Structure above to find the correct filename and the chapter title. Translate the surrounding text.

VISUAL EMPHASIS: Use mermaid diagrams to support learning. Stick to these three simple types:
- **Flowcharts** for showing decision-making or process flows
- **Class diagrams** for showing object or data relationships
- **Sequence diagrams** for step-by-step call flow between components

Use only these and keep each diagram minimal and beginner-friendly.

Heavily use analogies and examples throughout to help beginners understand.

End the chapter with a brief conclusion that summarizes what was learned and provides a transition to the next chapter. If there is a next chapter, use a proper Markdown link: Next Chapter Title.

Ensure the tone is welcoming and easy for a newcomer to understand.

Return the response as a JSON object in this exact format:

```json
{{
  "markdown_content": "The complete markdown content for the chapter goes here...",
  "summary": "A concise 2-3 sentence summary of what this chapter covers, including the main concepts and key takeaways for beginners."
}}
```
Now, directly provide a super beginner-friendly response in the JSON format above:
"""