1. Group files into semantically meaningful chunks
   ↓
2. Collect all important files
   ↓
3. Compute total token count
   ↓
4. IF total_token_count < 100K:
   → Use single LLM call to generate one abstraction
   (Returns: abstraction + list of all file names)
   ELSE:
   → For each chunk: - Generate abstraction (with file names tracked)
   → Combine all abstractions: - Inputs: abstraction text + file names - Output: final combined abstraction + full file list

   Chapter Generation!

5. Order abstractions pedagogically 
   ↓
6. For each abstraction in order:
   → Collect related files (based on abstraction files)
   → Build progressive context (summaries of previous chapters)
   → Generate individual chapter via LLM
   ↓
7. Combine all chapters into final tutorial structure
