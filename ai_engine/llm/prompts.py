"""
ai_engine/llm/prompts.py

Responsibility: every prompt template used anywhere in the engine, in
one place. Provider-agnostic - lives above the `llm/gemini.py`
abstraction, so if a second provider is ever added, both providers reuse
these exact same prompts (a prompt is a property of the TASK - "answer
grounded in context", "summarize", "make quiz questions" - not of which
model executes it).

Why explicit "if unknown, say X" instructions in the RAG prompt?
LLMs are trained to be maximally helpful, which means their default
behavior when context doesn't contain an answer is to fall back on
general world knowledge and hallucinate something plausible. A grounded
RAG system needs an explicit, literal escape hatch phrase - without one,
"be grounded" instructions alone are unreliable. `NO_ANSWER_MESSAGE` is
imported (not retyped) from `config.py` so the prompt's instruction and
`services/chat_service.py`'s fallback-detection logic can never drift
out of sync with each other.

Why a separate "partial answer" rule? A pure binary (full answer /
total refusal) is wrong for real study material, where context often
answers PART of a question. Refusing entirely when 60% of the question
is answerable is a worse tutoring experience than answering the
supported part and being explicit about the gap - so the escape hatch
is reserved for the case where NONE of the question is covered.
"""

from __future__ import annotations

from typing import List, Optional

from langchain_core.documents import Document

from ai_engine.config import NO_ANSWER_MESSAGE

# ---------------------------------------------------------------------
# Chat (RAG)
# ---------------------------------------------------------------------
_RAG_PROMPT_TEMPLATE = """You are a careful, factual study assistant answering a student's question using ONLY the context provided below.

RULES:
1. Answer using ONLY information found in the context. Do not use outside knowledge.
2. If the context does not contain ANY information relevant to the question, respond with EXACTLY this sentence and nothing else:
   "{no_answer_message}"
3. If the context PARTIALLY answers the question, answer what it supports, then explicitly state what part of the question isn't covered by the material - do not use the no-answer message unless none of the question is answerable.
4. Give a clear, well-structured explanation using all relevant information from the context.
5. Organize the answer with headings or bullet points when it improves clarity.
6. Do not mention "the context" or "the documents" in your answer - answer as if you simply know the material. When noting a gap (rule 3), phrase it as "the material doesn't cover X" rather than "the context doesn't contain X".

CONTEXT:
{context}

{chat_history}QUESTION:
{question}

ANSWER:
"""


def _format_context(documents: List[Document]) -> str:
    """Turn retrieved chunks into one context block, tagging each chunk
    with its source so answers stay traceable, even though the prompt
    itself instructs the model not to mention "the context" in its
    final answer text - traceability happens at the citation layer
    (`utils.helpers.format_sources`), not inside the generated answer.
    """
    blocks = []
    for i, doc in enumerate(documents, start=1):
        source = doc.metadata.get("source", "unknown")
        blocks.append(f"[Chunk {i} | source: {source}]\n{doc.page_content}")
    return "\n\n".join(blocks)


def _format_history(history: Optional[List[dict]]) -> str:
    """Format recent conversation turns if present."""
    if not history:
        return ""
    lines = ["RECENT CONVERSATION HISTORY:"]
    for turn in history:
        role = turn.get("role", "user").capitalize()
        content = turn.get("content", "").strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines) + "\n\n"


def build_rag_prompt(
    question: str,
    documents: List[Document],
    history: Optional[List[dict]] = None,
) -> str:
    """Build the final chat prompt sent to the LLM."""
    context = _format_context(documents) if documents else "(no relevant context retrieved)"
    chat_history = _format_history(history)
    return _RAG_PROMPT_TEMPLATE.format(
        no_answer_message=NO_ANSWER_MESSAGE,
        context=context,
        chat_history=chat_history,
        question=question,
    )


# ---------------------------------------------------------------------
# Summarization (map-reduce)
# ---------------------------------------------------------------------
_SUMMARY_MAP_PROMPT_TEMPLATE = """Summarize the following portion of study material concisely, preserving key facts, definitions, and any numbers or examples.

TEXT:
{text}

CONCISE SUMMARY:
"""

_SUMMARY_COMBINE_PROMPT_TEMPLATE = """You are an expert study assistant. Combine the following partial summaries into one complete, well-organized summary of the whole material.

Use clear section headings and bullet points where helpful. Do not repeat information across sections.

PARTIAL SUMMARIES:
{summaries}

FINAL SUMMARY:
"""


def build_summary_map_prompt(text_chunk: str) -> str:
    """Prompt for summarizing ONE chunk (the "map" step)."""
    return _SUMMARY_MAP_PROMPT_TEMPLATE.format(text=text_chunk)


def build_summary_combine_prompt(chunk_summaries: List[str]) -> str:
    """Prompt for combining all chunk summaries into one final summary
    (the "reduce" step).

    Short-circuits when there is exactly one chunk summary: combining a
    single summary with itself wastes an LLM call and risks the model
    "improving" wording it didn't need to touch. Callers get the chunk
    summary back unchanged instead.
    """
    if len(chunk_summaries) == 1:
        return chunk_summaries[0]

    summaries_block = "\n\n".join(
        f"[Part {i}]\n{summary}" for i, summary in enumerate(chunk_summaries, start=1)
    )
    return _SUMMARY_COMBINE_PROMPT_TEMPLATE.format(summaries=summaries_block)


# ---------------------------------------------------------------------
# Notes generation
# ---------------------------------------------------------------------
_NOTES_BULLET_PROMPT_TEMPLATE = """Turn the following study material into clear, well-organized bullet-point study notes.

Use headings for major topics, sub-bullets for supporting details, and bold the most important terms.

MATERIAL:
{text}

STUDY NOTES:
"""

_NOTES_CORNELL_PROMPT_TEMPLATE = """Turn the following study material into Cornell-style study notes with three clearly labeled sections:

1. "Cues" - key questions or keywords a student would use to quiz themselves.
2. "Notes" - the main detailed notes, organized by topic.
3. "Summary" - a short (3-5 sentence) summary of the whole material.

MATERIAL:
{text}

CORNELL NOTES:
"""


def build_notes_prompt(text: str, style: str = "bullet") -> str:
    """Prompt for generating study notes in the requested style.

    Args:
        text: the (already summarized or raw, depending on caller)
        material to turn into notes.
        style: "bullet" or "cornell".

    Raises:
        ValueError: if `style` is not a recognized notes style.
    """
    if style == "bullet":
        return _NOTES_BULLET_PROMPT_TEMPLATE.format(text=text)
    if style == "cornell":
        return _NOTES_CORNELL_PROMPT_TEMPLATE.format(text=text)
    raise ValueError(f"Unknown notes style: '{style}'. Must be 'bullet' or 'cornell'.")


# ---------------------------------------------------------------------
# Quiz generation
# ---------------------------------------------------------------------
# Difficulty is spelled out explicitly rather than left as a bare label
# ("easy"/"medium"/"hard" mean nothing consistent to a model without a
# definition - it will guess, and guess differently per subject).
_QUIZ_DIFFICULTY_DEFINITIONS = {
    "easy": "Basic recall, definitions, fundamental concepts, and straightforward questions stated explicitly in the material requiring no complex inference.",
    "medium": "Conceptual understanding, application of concepts, moderate reasoning, and comparison questions connecting distinct facts from the material.",
    "hard": "Deeper reasoning, multi-concept synthesis, scenario-based questions, and challenging application of concepts to new examples.",
}

_QUIZ_PROMPT_TEMPLATE = """Based ONLY on the study material below, write exactly {question_count} multiple-choice quiz questions at {difficulty} difficulty.

Difficulty definition for "{difficulty}": {difficulty_definition}

Respond with ONLY a raw JSON array (no Markdown code fences, no commentary) where each element has this exact shape:
{{
  "question": "...",
  "options": ["...", "...", "...", "..."],
  "correct_answer_index": 0,
  "explanation": "..."
}}

Each question must have exactly 4 options, exactly one correct answer, and a short explanation of why that answer is correct.

IMPORTANT: Vary correct_answer_index across the {question_count} questions - do not place the correct answer in the same position every time. Distribute correct answers roughly evenly across indices 0-3.

MATERIAL:
{text}

JSON ARRAY:
"""


def build_quiz_prompt(text: str, question_count: int, difficulty: str) -> str:
    """Prompt for generating a structured, JSON-parseable quiz.

    Args:
        text: source material to generate questions from.
        question_count: how many questions to generate.
        difficulty: one of the values in `config.QUIZ_DIFFICULTY_LEVELS`
        ("easy", "medium", "hard").

    Raises:
        KeyError: if `difficulty` has no entry in
        `_QUIZ_DIFFICULTY_DEFINITIONS` - fail loudly rather than send
        the model an undefined difficulty label.

    Note: if the LLM provider (`llm/gemini.py`) supports native
    structured output (e.g. Gemini's `response_schema`), prefer that
    over parsing this raw-JSON-in-prompt approach - it removes an
    entire class of "model added a code fence anyway" parsing failures.
    This template is the fallback for providers without that feature.
    """
    try:
        difficulty_definition = _QUIZ_DIFFICULTY_DEFINITIONS[difficulty]
    except KeyError:
        raise KeyError(
            f"Unknown quiz difficulty: '{difficulty}'. "
            f"Must be one of {list(_QUIZ_DIFFICULTY_DEFINITIONS)}."
        ) from None

    return _QUIZ_PROMPT_TEMPLATE.format(
        question_count=question_count,
        difficulty=difficulty,
        difficulty_definition=difficulty_definition,
        text=text,
    )