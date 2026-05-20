"""LLM semantic diff engine — describes what *meaning* changed between prompts."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime

from pgit.objects import SemanticDiff, hash_blob
from pgit.store import ObjectStore

SYSTEM_PROMPT = """
You are a prompt engineering expert. You will be given two versions of an LLM
system prompt and must describe exactly what changed in meaning between them.

Focus on:
- New rules or constraints added
- Rules or constraints removed
- Tone or style shifts
- Structural reorganisation that changes how instructions are read
- Changes to examples or few-shot demonstrations
- Changes to persona or role definition

Do NOT describe formatting changes (whitespace, punctuation) unless they
affect meaning. Be concise and specific.

Respond ONLY with valid JSON matching this schema:
{
  "summary": "one sentence describing the most important change",
  "additions": ["list of new concepts or rules added"],
  "removals": ["list of concepts or rules removed"],
  "tone_shift": "description of tone change, or null",
  "structural_changes": ["list of structural changes that affect meaning"]
}
"""


def generate_semantic_diff(
    from_text: str,
    to_text: str,
    store: ObjectStore,
    from_format: str = "plaintext",
    to_format: str = "plaintext",
) -> SemanticDiff:
    """Generate a semantic diff between two prompt texts using an LLM.

    Results are cached in the store — same inputs always return cached result.
    Requires PGIT_LLM_KEY environment variable to be set.
    """
    from_hash = hash_blob(from_text, from_format, None)
    to_hash = hash_blob(to_text, to_format, None)
    cache_key = f"{from_hash}:{to_hash}"

    # Check cache first — semantic diffs are expensive
    cached = store.get_semantic_diff(cache_key)
    if cached is not None:
        return cached

    # Get API key
    api_key = os.environ.get("PGIT_LLM_KEY")
    if not api_key:
        raise RuntimeError(
            "PGIT_LLM_KEY environment variable is required for semantic diff. "
            "Set it to your Anthropic API key."
        )

    model = os.environ.get("PGIT_LLM_MODEL", "claude-haiku-4-5-20251001")

    try:
        import anthropic  # type: ignore[import-not-found]
    except ImportError:
        raise RuntimeError(
            "The 'anthropic' package is required for semantic diff. "
            "Install it with: pip install prompt-git[semantic]"
        )

    client = anthropic.Anthropic(api_key=api_key)
    response = client.messages.create(
        model=model,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": f"BEFORE:\n{from_text}\n\nAFTER:\n{to_text}",
            }
        ],
    )

    # Parse the response — strip markdown code fences if present
    raw_text = response.content[0].text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    parsed = json.loads(raw_text)

    now = datetime.now(UTC).isoformat()
    diff = SemanticDiff(
        from_hash=from_hash,
        to_hash=to_hash,
        summary=parsed["summary"],
        additions=parsed.get("additions", []),
        removals=parsed.get("removals", []),
        tone_shift=parsed.get("tone_shift"),
        structural_changes=parsed.get("structural_changes", []),
        model_used=model,
        generated_at=now,
    )

    # Cache the result
    store.put_semantic_diff(diff)
    return diff
