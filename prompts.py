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