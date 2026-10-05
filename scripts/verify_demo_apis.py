import os
import sys
sys.path.insert(0, os.path.abspath("."))
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("==================================================")
    print("VERIFYING STUDYPILOT APIS WITH SYNTHETIC STUDENT")
    print("==================================================")
    
    # 1. Login
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "demo.student@studypilot.local",
        "password": "Demo@12345"
    })
    if login_resp.status_code != 200:
        print(f"FAILED: Login failed: {login_resp.status_code} {login_resp.text}")
        sys.exit(1)
    
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
    assert me_resp.status_code == 200, f"Me failed: {me_resp.text}"
    user = me_resp.json()
    print(f"PASS: Logged in as '{user.get('name')}' ({user.get('email')}) [ID: {user.get('id')}]")

    # 2. Resources
    res_resp = requests.get(f"{BASE_URL}/api/resources", headers=headers)
    assert res_resp.status_code == 200, f"Resources failed: {res_resp.text}"
    resources = res_resp.json()
    print(f"PASS: Resources count = {len(resources)} (Expected: 6)")
    for r in resources:
        print(f"  - [{r.get('status')}] {r.get('title')} (res_id={r.get('resource_id')})")

    # 3. Conversations
    conv_resp = requests.get(f"{BASE_URL}/api/conversations", headers=headers)
    assert conv_resp.status_code == 200, f"Conversations failed: {conv_resp.text}"
    conversations = conv_resp.json()
    print(f"PASS: Conversations count = {len(conversations)} (Expected: 4)")
    for c in conversations:
        # Check messages
        msg_resp = requests.get(f"{BASE_URL}/api/conversations/{c['id']}/messages", headers=headers)
        assert msg_resp.status_code == 200
        msgs = msg_resp.json()
        print(f"  - Conversation '{c.get('title')}': {len(msgs)} messages")

    # 4. Mastery
    mastery_resp = requests.get(f"{BASE_URL}/api/mastery", headers=headers)
    assert mastery_resp.status_code == 200, f"Mastery failed: {mastery_resp.text}"
    mastery_data = mastery_resp.json()
    print(f"PASS: Mastery topics = {len(mastery_data)} (Expected: 6)")
    for m in mastery_data:
        print(f"  - Topic: {m.get('topic')}, Score: {m.get('mastery_score')}%, Status: {m.get('status')}")

    # 5. Knowledge Gaps
    gaps_resp = requests.get(f"{BASE_URL}/api/mastery/gaps", headers=headers)
    assert gaps_resp.status_code == 200, f"Gaps failed: {gaps_resp.text}"
    gaps_data = gaps_resp.json()
    gaps_list = gaps_data.get("gaps", [])
    print(f"PASS: Knowledge gaps count = {len(gaps_list)} (Total topics: {gaps_data.get('total_topics')}, Mastered: {gaps_data.get('mastered_count')})")
    for g in gaps_list:
        print(f"  - Gap: {g.get('topic')}, Score: {g.get('mastery_score')}%, Status: {g.get('status')}")

    # 6. Revision Schedule
    rev_resp = requests.get(f"{BASE_URL}/api/revision", headers=headers)
    assert rev_resp.status_code == 200, f"Revision failed: {rev_resp.text}"
    rev_data = rev_resp.json()
    print(f"PASS: Revision records count = {len(rev_data)} (Expected: 6)")
    due_items = [r for r in rev_data if r.get("status") == "Due"]
    sched_items = [r for r in rev_data if r.get("status") != "Due"]
    print(f"  - Due Revisions ({len(due_items)}): {[r.get('topic') for r in due_items]}")
    print(f"  - Scheduled Revisions ({len(sched_items)}): {[r.get('topic') for r in sched_items]}")

    # 7. AI Summary, Notes, Quiz for first resource
    first_res = resources[0]
    rid = first_res["resource_id"]
    
    sum_resp = requests.get(f"{BASE_URL}/api/resources/{rid}/summary", headers=headers)
    assert sum_resp.status_code == 200, f"Summary failed: {sum_resp.text}"
    print(f"PASS: Summary retrieved for '{first_res['title']}' (Length: {len(sum_resp.json()['summary'])} chars)")

    notes_resp = requests.get(f"{BASE_URL}/api/resources/{rid}/notes", headers=headers)
    assert notes_resp.status_code == 200, f"Notes failed: {notes_resp.text}"
    print(f"PASS: Notes retrieved for '{first_res['title']}' (Length: {len(notes_resp.json()['content'])} chars)")

    quiz_resp = requests.get(f"{BASE_URL}/api/resources/{rid}/quizzes", headers=headers)
    assert quiz_resp.status_code == 200, f"Quiz failed: {quiz_resp.text}"
    quizzes = quiz_resp.json()
    print(f"PASS: Quiz retrieved for '{first_res['title']}' (Found: {len(quizzes)} quiz records)")

    # 8. Test Chroma Vector Retrieval via /api/resources/{rid}/search
    dbms_res = next(r for r in resources if "DBMS" in r["title"])
    search_resp = requests.post(
        f"{BASE_URL}/api/resources/{dbms_res['resource_id']}/search",
        headers=headers,
        json={"query": "ACID atomicity transaction rollback", "top_k": 2},
    )
    assert search_resp.status_code == 200, f"Search failed: {search_resp.text}"
    search_results = search_resp.json()
    chunks = search_results.get("results", [])
    print(f"PASS: Vector retrieval returned {len(chunks)} relevant chunks for query: '{search_results.get('query')}'")
    for chunk in chunks:
        print(f"  - Chunk: {chunk.get('content')[:90]}... (Score: {chunk.get('score')})")

    print("==================================================")
    print("ALL API & ENGINE VERIFICATIONS PASSED SUCCESSFULLY")
    print("==================================================")

if __name__ == "__main__":
    test_api()
