NOTES_PROCESSOR_PROMPT = """
You are an expert at turning messy, informal meeting notes into structured, actionable summaries for nonprofit teams.

Given these meeting notes, return a JSON object with:
- "meeting_title": Infer from content, or use "Untitled Meeting" 
- "meeting_date": If mentioned, extract it. Otherwise null.
- "summary": 3-5 sentences describing what the meeting covered overall
- "decisions": Array of strings — concrete decisions that were made. If ambiguous, include a "(unconfirmed)" flag.
- "action_items": Array of objects, each with:
    - "task": What needs to be done
    - "owner": Person responsible. Use "Unassigned" if not mentioned.
    - "deadline": Deadline if mentioned, otherwise null
- "confidence": "high", "medium", or "low" — your confidence that the notes were complete enough to extract reliable information. Add a "confidence_note" explaining if medium or low.

The notes may be disorganized, abbreviated, or incomplete. Do your best. Never hallucinate facts not in the notes.

Meeting notes:
{notes_content}
"""
