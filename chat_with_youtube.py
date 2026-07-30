"""
chat_with_youtube.py

Manual end-to-end check: ingest a YouTube video, then chat with it.
Prints which transcription path was used (captions vs Whisper fallback)
so you can confirm both paths actually work.

Run: python chat_with_youtube.py
"""

from ai_engine.engine import AIEngine

engine = AIEngine()
engine.initialize()

# Replace with a real YouTube URL. Pick one you know HAS captions first
# (most lecture/tutorial videos do) to test the fast path.
YOUTUBE_URL = "https://youtu.be/gieEQFIfgYc?si=lNnj-GSxz5dQWwzU"

result = engine.ingest(YOUTUBE_URL)
print(f"\nIngested: {result.source}")
print(f"resource_id: {result.resource_id}")
print(f"chunks created: {result.chunks_created}")

# Confirm which transcription path was actually used - this is the
# interesting bit for this test.
docs = engine.search("test", resource_id=result.resource_id, top_k=1)
if docs:
    transcript_source = docs[0].metadata.get("transcript_source", "unknown")
    print(f"Transcript source: {transcript_source}  (captions = fast path, whisper = fallback)")

while True:
    question = input("\nAsk a question (or 'quit'): ")
    if question.lower() == "quit":
        break
    response = engine.chat(question, resource_id=result.resource_id)
    print(f"\nAnswer: {response.answer}")
    print(f"Grounded: {response.was_grounded}")