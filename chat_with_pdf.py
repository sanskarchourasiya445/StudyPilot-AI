"""
chat_with_pdf.py

Manual end-to-end check: ingest a real PDF, then chat with it.
Run: python chat_with_pdf.py
"""

from ai_engine.engine import AIEngine

engine = AIEngine()
engine.initialize()

# Replace with a real path to a PDF on your machine.
PDF_PATH = r"C:\Projects\RAG\data\documents\mongodbnotes.pdf"

result = engine.ingest(PDF_PATH)
print(f"Ingested: {result.source}")
print(f"resource_id: {result.resource_id}")
print(f"chunks created: {result.chunks_created}")

while True:
    question = input("\nAsk a question (or 'quit'): ")
    if question.lower() == "quit":
        break
    response = engine.chat(question, resource_id=result.resource_id)
    print(f"\nAnswer: {response.answer}")
    print(f"Grounded: {response.was_grounded}")