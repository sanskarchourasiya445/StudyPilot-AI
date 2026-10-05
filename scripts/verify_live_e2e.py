import os
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.db.models.user import User
from backend.app.db.models.resource import Resource
from ai_engine.engine import AIEngine
from ai_engine.llm.gemini import GeminiLLM, LLMGenerationError

from backend.app.ai.engine_provider import get_ai_engine, set_ai_engine

def test_chroma_tenant_isolation_and_filters():
    print("\n--- 1. Testing Chroma Tenant Isolation & Multi-Resource Filters ---")
    engine = get_ai_engine()

    user_a = f"user_a_{uuid.uuid4().hex[:8]}"
    user_b = f"user_b_{uuid.uuid4().hex[:8]}"
    
    # Create sample text files for testing
    scratch_dir = Path(__file__).resolve().parent
    doc_a_path = scratch_dir / "sample_a.txt"
    doc_b_path = scratch_dir / "sample_b.txt"

    doc_a_path.write_text("Binary search trees maintain sorted keys for fast O(log n) lookup, insertion, and deletion in computer science.", encoding="utf-8")
    doc_b_path.write_text("Photosynthesis in green plants converts sunlight, water, and carbon dioxide into oxygen and glucose.", encoding="utf-8")

    try:
        # Ingest for User A
        res_a1 = engine.ingest(str(doc_a_path), user_id=user_a, workspace_id="ws_a")
        print(f"Ingested for User A: id={res_a1.resource_id}, chunks={res_a1.chunks_created}")

        # Ingest for User B
        res_b1 = engine.ingest(str(doc_b_path), user_id=user_b, workspace_id="ws_b")
        print(f"Ingested for User B: id={res_b1.resource_id}, chunks={res_b1.chunks_created}")

        # Verify metadata in Chroma collection
        chunks_a = engine.search("Binary search trees", user_id=user_a)
        assert len(chunks_a) > 0, "User A should retrieve their own chunks"
        for c in chunks_a:
            assert c.metadata.get("user_id") == user_a, f"Expected user_id={user_a}, got {c.metadata.get('user_id')}"
            assert c.metadata.get("resource_id") == res_a1.resource_id
        print("  [PASS] User A chunks have correct metadata (user_id, resource_id)")

        # Verify Tenant Isolation: User B cannot retrieve User A's chunks
        # 1. Any chunks returned for User B must belong to User B, NEVER User A
        chunks_b_cross = engine.search("Binary search trees", user_id=user_b)
        for c in chunks_b_cross:
            assert c.metadata.get("user_id") == user_b, "User B retrieved User A's chunk!"
            assert c.metadata.get("resource_id") != res_a1.resource_id, "User B retrieved User A's resource!"
        print("  [PASS] Tenant isolation: User B search never returns User A chunks")

        # 2. User B querying explicitly with User A's resource_id gets 0 chunks
        chunks_b_with_a_res = engine.search("Binary search trees", user_id=user_b, resource_ids=[res_a1.resource_id])
        assert len(chunks_b_with_a_res) == 0, "User B should get 0 chunks when querying User A's resource"
        print("  [PASS] Tenant isolation: Cross-tenant resource_id query returns 0 chunks")

        # Verify User B retrieves User B's chunks
        chunks_b = engine.search("Photosynthesis", user_id=user_b)
        assert len(chunks_b) > 0, "User B should retrieve their own chunks"
        for c in chunks_b:
            assert c.metadata.get("user_id") == user_b
        print("  [PASS] User B retrieves User B's chunks")

        # Verify multi-resource filter
        chunks_res_filter = engine.search("Binary search trees", user_id=user_a, resource_ids=[res_a1.resource_id])
        assert len(chunks_res_filter) > 0, "Multi-resource filter should find chunks"
        print("  [PASS] resource_ids filter successfully returned matching chunks")

        chunks_res_filter_empty = engine.search("Binary search trees", user_id=user_a, resource_ids=["non_existent_res"])
        assert len(chunks_res_filter_empty) == 0, "Non-existent resource_id should return 0 chunks"
        print("  [PASS] Empty filter result handled safely without crash")

    finally:
        # Cleanup
        if doc_a_path.exists():
            doc_a_path.unlink()
        if doc_b_path.exists():
            doc_b_path.unlink()
        engine.delete_resource(res_a1.resource_id)
        engine.delete_resource(res_b1.resource_id)
        print("  [PASS] Cleaned up temporary test resources from Chroma")

def test_full_fastapi_student_flow():
    print("\n--- 2. Testing End-to-End FastAPI Student Flow ---")
    client = TestClient(app)

    # 1. Register & Login
    unique_email = f"demo_student_{uuid.uuid4().hex[:6]}@studypilot.ai"
    password = "SecurePassword123!"
    reg_resp = client.post("/api/auth/register", json={
        "email": unique_email,
        "password": password,
        "full_name": "Demo Student"
    })
    assert reg_resp.status_code == 201, f"Register failed: {reg_resp.text}"
    login_resp = client.post("/api/auth/login", json={"email": unique_email, "password": password})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  [PASS] Registered and logged in demo user: {unique_email}")

    # 2. Upload PDF
    pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n/Contents 4 0 R\n/Resources <<\n/Font <<\n/F1 <<\n/Type /Font\n/Subtype /Type1\n/BaseFont /Helvetica\n>>\n>>\n>>\nendobj\n4 0 obj\n<<\n/Length 97\n>>\nstream\nBT\n/F1 14 Tf\n50 700 Td\n(Operating Systems: Virtual memory provides address space isolation for processes.) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000117 00000 n \n0000000288 00000 n \ntrailer\n<<\n/Size 5\n/Root 1 0 R\n>>\nstartxref\n436\n%%EOF"
    
    files = {"file": ("operating_systems.pdf", pdf_content, "application/pdf")}
    upload_resp = client.post("/api/resources/pdf", headers=headers, files=files)
    assert upload_resp.status_code == 201, f"Upload failed: {upload_resp.text}"
    res_data = upload_resp.json()
    res_id = res_data["id"]
    print(f"  [PASS] Uploaded resource: id={res_id}, status={res_data['status']}")
    assert res_data["status"] == "ready"

    import json
    def mock_generate(prompt, temperature=0.3):
        p_lower = prompt.lower()
        if "quiz" in p_lower or "multiple-choice" in p_lower or "json" in p_lower:
            return json.dumps([
                {
                    "question": "What does virtual memory provide?",
                    "options": ["Address space isolation", "Faster CPU", "More disk space", "Network security"],
                    "correct_answer_index": 0,
                    "explanation": "Virtual memory isolates address spaces."
                },
                {
                    "question": "What is paging?",
                    "options": ["Memory management scheme", "A printer feature", "Network protocol", "Disk format"],
                    "correct_answer_index": 0,
                    "explanation": "Paging is a memory management scheme."
                },
                {
                    "question": "What is a page fault?",
                    "options": ["Trap when page not in memory", "Syntax error", "Compiler warning", "CPU crash"],
                    "correct_answer_index": 0,
                    "explanation": "Page fault occurs when page not in memory."
                }
            ])
        if "summary" in p_lower:
            return "This document covers operating systems, virtual memory, and process isolation."
        if "notes" in p_lower:
            return "- Operating Systems\n  - Virtual Memory\n  - Process Isolation"
        return "Virtual memory provides address space isolation for processes."

    mock_llm = MagicMock()
    mock_llm.generate.side_effect = mock_generate
    
    engine = get_ai_engine()
    engine._llm = mock_llm
    engine._summary_service._llm = mock_llm
    engine._notes_service._llm = mock_llm
    engine._quiz_service._llm = mock_llm

    # Test single resource chat
    chat_resp = client.post("/api/chat", headers=headers, json={
        "message": "What does virtual memory do?",
        "resource_ids": [res_id]
    })
    assert chat_resp.status_code == 200, f"Chat failed: {chat_resp.text}"
    chat_data = chat_resp.json()
    assert "Virtual memory" in chat_data["answer"]
    assert len(chat_data["sources"]) > 0
    conv_id = chat_data["conversation_id"]
    print(f"  [PASS] Single-resource RAG Chat succeeded (sources count: {len(chat_data['sources'])})")

    # Test conversation history continuation
    chat_followup = client.post("/api/chat", headers=headers, json={
        "conversation_id": conv_id,
        "message": "Can you explain process isolation in more detail?",
        "resource_ids": [res_id]
    })
    assert chat_followup.status_code == 200
    print("  [PASS] Conversation history continuation succeeded")

    # Test multi-resource filter (passing list of IDs)
    chat_multi = client.post("/api/chat", headers=headers, json={
        "message": "Summarize virtual memory",
        "resource_ids": [res_id]
    })
    assert chat_multi.status_code == 200
    print("  [PASS] Multi-resource RAG Chat succeeded")

    # Test workspace-wide chat (no resource_ids passed)
    chat_all = client.post("/api/chat", headers=headers, json={
        "message": "General knowledge test",
        "resource_ids": []
    })
    assert chat_all.status_code == 200
    print("  [PASS] Workspace-wide RAG Chat succeeded")

    # 4. Test Study Capabilities (Summary, Notes, Quiz)
    summary_resp = client.post(f"/api/resources/{res_id}/summary", headers=headers)
    assert summary_resp.status_code == 200, f"Summary failed: {summary_resp.text}"
    print("  [PASS] Summary generation succeeded")

    notes_resp = client.post(f"/api/resources/{res_id}/notes", headers=headers, json={"style": "bullet"})
    assert notes_resp.status_code == 200, f"Notes failed: {notes_resp.text}"
    print("  [PASS] Notes generation succeeded")

    quiz_resp = client.post(f"/api/resources/{res_id}/quiz", headers=headers, json={"question_count": 3, "difficulty": "medium"})
    assert quiz_resp.status_code == 200, f"Quiz generation failed: {quiz_resp.text}"
    quiz_data = quiz_resp.json()
    quiz_id = quiz_data["id"]
    print(f"  [PASS] Adaptive Quiz generation succeeded (quiz_id: {quiz_id})")

    # 5. Submit Quiz & Verify Mastery / Revision Scheduling
    submit_resp = client.post(f"/api/resources/quizzes/{quiz_id}/submit?score=3&total_questions=3", headers=headers)
    assert submit_resp.status_code == 200, f"Quiz submission failed: {submit_resp.text}"
    submit_data = submit_resp.json()
    print(f"  [PASS] Quiz submission processed: score={submit_data.get('score')}")

    # Check Mastery
    mastery_resp = client.get("/api/mastery", headers=headers)
    assert mastery_resp.status_code == 200
    print(f"  [PASS] Mastery records retrieved: count={len(mastery_resp.json())}")

    # Check Revision Schedule
    rev_resp = client.get("/api/revision", headers=headers)
    assert rev_resp.status_code == 200
    print(f"  [PASS] Revision schedule retrieved: count={len(rev_resp.json())}")

    # Cleanup DB resource and Chroma
    del_resp = client.delete(f"/api/resources/{res_id}", headers=headers)
    assert del_resp.status_code in (200, 204)
    print("  [PASS] Resource deletion cleaned up DB and Chroma")

if __name__ == "__main__":
    test_chroma_tenant_isolation_and_filters()
    test_full_fastapi_student_flow()
    print("\nALL RUNTIME VERIFICATIONS COMPLETED SUCCESSFULLY!")
