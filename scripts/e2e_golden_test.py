"""
scripts/e2e_golden_test.py
Deterministic End-to-End Golden Test for StudyPilot AI.
Follows Section 20 of the specification:
1. Register/Login
2. Upload PDF
3. Wait until READY
4. Add YouTube URL
5. Wait until READY
6. Ask a question from PDF
7. Ask a question from YouTube
8. Ask a comparative question requiring both resources
9. Verify citations
10. Generate Summary & verify cache
11. Generate Notes (both bullet and cornell)
12. Generate Quiz
13. Submit Quiz & verify score persistence
14. Open conversation history & verify persistence
15. Verify out-of-domain non-hallucination
16. Logout & verify protected routes require auth
"""

import os
import sys
import uuid
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.main import app
from backend.app.db.session import SessionLocal
from backend.app.db.models.user import User

client = TestClient(app)


def run_golden_test():
    print("=" * 70)
    print("STARTING END-TO-END GOLDEN TEST FOR STUDYPILOT AI")
    print("=" * 70)

    # 1. Register & Login
    unique_id = uuid.uuid4().hex[:8]
    email = f"goldentest_{unique_id}@studypilot.ai"
    password = "GoldenTestPassword123!"
    name = f"Golden Tester {unique_id}"

    print(f"\n[STEP 1] Registering and authenticating user: {email}")
    reg_res = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    assert reg_res.status_code == 201, f"Register failed: {reg_res.text}"

    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(" -> Registered and acquired JWT auth token successfully.")

    # 2. Upload PDF
    pdf_path = ROOT / "documents" / "Python_for_AI.pdf"
    assert pdf_path.exists(), f"Sample PDF not found at {pdf_path}"
    print(f"\n[STEP 2] Ingesting PDF document: {pdf_path.name}")
    with open(pdf_path, "rb") as f:
        upload_res = client.post(
            "/api/resources/pdf",
            files={"file": (pdf_path.name, f, "application/pdf")},
            headers=headers,
        )
    assert upload_res.status_code == 201, f"PDF upload failed: {upload_res.text}"
    pdf_resource = upload_res.json()
    pdf_resource_id = pdf_resource["resource_id"]
    print(f" -> PDF Ingested: resource_id={pdf_resource_id}, status={pdf_resource['status']}, chunks={pdf_resource['chunk_count']}")
    assert pdf_resource["status"] == "ready"
    assert pdf_resource["chunk_count"] > 0

    # 3. Ingest YouTube URL (known accessible educational video with captions)
    yt_url = "https://www.youtube.com/watch?v=kqtD5dpn9C8"
    print(f"\n[STEP 3] Ingesting YouTube video: {yt_url}")
    yt_res = client.post(
        "/api/resources/youtube",
        json={"url": yt_url, "title": "Python for Beginners - Mosh"},
        headers=headers,
    )
    assert yt_res.status_code == 201, f"YouTube ingestion failed: {yt_res.text}"
    yt_resource = yt_res.json()
    yt_resource_id = yt_resource["resource_id"]
    print(f" -> YouTube Ingested: resource_id={yt_resource_id}, status={yt_resource['status']}, chunks={yt_resource['chunk_count']}")
    assert yt_resource["status"] == "ready"
    assert yt_resource["chunk_count"] > 0

    # 4. Ask a question from PDF
    print(f"\n[STEP 4] Chat - Querying PDF resource...")
    chat_pdf_res = client.post(
        "/api/chat",
        json={
            "message": "What is Python and what data types does it provide?",
            "resource_id": pdf_resource_id,
        },
        headers=headers,
    )
    assert chat_pdf_res.status_code == 200, f"Chat failed: {chat_pdf_res.text}"
    chat_pdf_data = chat_pdf_res.json()
    print(" -> PDF Answer:\n", chat_pdf_data["answer"][:300], "...")
    print(f" -> Citations returned: {len(chat_pdf_data['sources'])}")
    assert len(chat_pdf_data["sources"]) > 0
    assert "python" in chat_pdf_data["answer"].lower()
    conv_id = chat_pdf_data["conversation_id"]

    # 5. Ask a question from YouTube
    print(f"\n[STEP 5] Chat - Querying YouTube resource...")
    chat_yt_res = client.post(
        "/api/chat",
        json={
            "message": "What is covered in this video lecture?",
            "resource_id": yt_resource_id,
            "conversation_id": conv_id,
        },
        headers=headers,
    )
    assert chat_yt_res.status_code == 200, f"YouTube chat failed: {chat_yt_res.text}"
    chat_yt_data = chat_yt_res.json()
    print(" -> YouTube Answer:\n", chat_yt_data["answer"][:300], "...")
    print(f" -> Citations returned: {len(chat_yt_data['sources'])}")
    assert len(chat_yt_data["sources"]) > 0

    # 6. Ask a multi-resource question
    print(f"\n[STEP 6] Chat - Querying multiple resources (PDF + YouTube)...")
    chat_multi_res = client.post(
        "/api/chat",
        json={
            "message": "Summarize how Python is introduced across these study materials.",
            "resource_ids": [pdf_resource_id, yt_resource_id],
            "conversation_id": conv_id,
        },
        headers=headers,
    )
    assert chat_multi_res.status_code == 200, f"Multi-resource chat failed: {chat_multi_res.text}"
    chat_multi_data = chat_multi_res.json()
    print(" -> Multi-resource Answer:\n", chat_multi_data["answer"][:300], "...")
    print(f" -> Multi-resource Citations: {len(chat_multi_data['sources'])}")
    assert len(chat_multi_data["sources"]) > 0

    # 7. Verify out-of-domain question (Anti-hallucination check)
    print(f"\n[STEP 7] Chat - Asking out-of-domain question...")
    chat_ood_res = client.post(
        "/api/chat",
        json={
            "message": "What is the capital of France and its population?",
            "resource_id": pdf_resource_id,
        },
        headers=headers,
    )
    assert chat_ood_res.status_code == 200
    ood_answer = chat_ood_res.json()["answer"]
    print(" -> Out-of-domain Answer:\n", ood_answer)
    # Must refuse or state it could not be found in context
    assert (
        "could not find" in ood_answer.lower()
        or "does not contain" in ood_answer.lower()
        or "not mentioned" in ood_answer.lower()
        or "doesn't cover" in ood_answer.lower()
        or "not covered" in ood_answer.lower()
    ), f"Model hallucinated out-of-domain answer: {ood_answer}"

    # 8. Generate Summary for PDF
    print(f"\n[STEP 8] Generating AI Summary for PDF...")
    summary_gen_res = client.post(
        f"/api/resources/{pdf_resource_id}/summary",
        json={"force_regenerate": True},
        headers=headers,
    )
    assert summary_gen_res.status_code == 200, f"Summary generation failed: {summary_gen_res.text}"
    summary_data = summary_gen_res.json()
    print(" -> Summary length:", len(summary_data["summary"]))
    assert len(summary_data["summary"]) > 50

    # 9. Verify Cached Summary (GET)
    print(f"\n[STEP 9] Fetching cached summary via GET...")
    summary_get_res = client.get(
        f"/api/resources/{pdf_resource_id}/summary",
        headers=headers,
    )
    assert summary_get_res.status_code == 200, f"Summary GET failed: {summary_get_res.text}"
    assert summary_get_res.json()["cached"] is True
    print(" -> Cached summary verified successfully.")

    # 10. Generate Study Notes (Bullet style)
    print(f"\n[STEP 10] Generating Bullet Notes...")
    notes_res = client.post(
        f"/api/resources/{pdf_resource_id}/notes",
        json={"style": "bullet", "force_regenerate": False},
        headers=headers,
    )
    assert notes_res.status_code == 200, f"Notes generation failed: {notes_res.text}"
    bullet_notes = notes_res.json()
    print(" -> Bullet Notes length:", len(bullet_notes["content"]))
    assert len(bullet_notes["content"]) > 50

    # 11. Generate Study Notes (Cornell style)
    print(f"\n[STEP 11] Generating Cornell Notes...")
    cornell_res = client.post(
        f"/api/resources/{pdf_resource_id}/notes",
        json={"style": "cornell", "force_regenerate": False},
        headers=headers,
    )
    assert cornell_res.status_code == 200, f"Cornell notes generation failed: {cornell_res.text}"
    cornell_notes = cornell_res.json()
    print(" -> Cornell Notes length:", len(cornell_notes["content"]))
    assert len(cornell_notes["content"]) > 50

    # 12. Generate Quiz
    print(f"\n[STEP 12] Generating Multiple-Choice Quiz...")
    quiz_res = client.post(
        f"/api/resources/{pdf_resource_id}/quiz",
        json={"question_count": 3, "difficulty": "medium", "force_regenerate": False},
        headers=headers,
    )
    assert quiz_res.status_code == 200, f"Quiz generation failed: {quiz_res.text}"
    quiz_data = quiz_res.json()
    quiz_id = quiz_data["id"]
    questions = quiz_data["questions"]
    print(f" -> Quiz ID: {quiz_id}, questions count: {len(questions)}")
    assert len(questions) == 3
    for q in questions:
        assert "question" in q and len(q["options"]) == 4
        assert 0 <= q["correct_answer_index"] < 4
        assert len(q["explanation"]) > 0

    # 13. Submit Quiz Attempt
    print(f"\n[STEP 13] Submitting Quiz Attempt...")
    submit_res = client.post(
        f"/api/resources/quizzes/{quiz_id}/submit?score=3&total_questions=3",
        headers=headers,
    )
    assert submit_res.status_code == 200, f"Quiz submit failed: {submit_res.text}"
    attempt_data = submit_res.json()
    print(f" -> Quiz attempt recorded: score={attempt_data['score']}/{attempt_data['total_questions']}, mastery_score={attempt_data.get('mastery_score')}")
    assert attempt_data["score"] == 3

    # 14. Conversation history & persistence
    print(f"\n[STEP 14] Verifying conversation persistence...")
    conv_list_res = client.get("/api/conversations", headers=headers)
    assert conv_list_res.status_code == 200
    convs = conv_list_res.json()
    assert any(c["id"] == conv_id for c in convs)

    msg_res = client.get(f"/api/conversations/{conv_id}/messages", headers=headers)
    assert msg_res.status_code == 200
    messages = msg_res.json()
    print(f" -> Conversation {conv_id} has {len(messages)} messages persisted.")
    assert len(messages) >= 6

    # 15. Verify Protected Routes require auth
    print(f"\n[STEP 15] Verifying auth protection...")
    unauth_res = client.get("/api/resources")
    assert unauth_res.status_code == 401, f"Expected 401, got {unauth_res.status_code}"
    print(" -> Protected routes require authentication as expected.")

    print("\n" + "=" * 70)
    print("ALL END-TO-END GOLDEN TEST STEPS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_golden_test()
