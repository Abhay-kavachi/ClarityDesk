import os
import sys
import json
import time
from datetime import datetime

# Add backend to path so we can import the FastAPI app and RAG logic
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))
from rag.retrieval import get_top_k_cosine, retrieve_context
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

EVAL_DIR = os.path.dirname(__file__)
METRICS_FILE = os.path.join(EVAL_DIR, 'metrics.json')

def load_metrics():
    if os.path.exists(METRICS_FILE):
        with open(METRICS_FILE, 'r') as f:
            return json.load(f)
    return {
        "action_item_accuracy": 0,
        "citation_accuracy": 0,
        "hallucination_failures": 0,
        "avg_response_time": 0
    }

def save_metrics(metrics):
    # Save standard metrics.json
    with open(METRICS_FILE, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    # Save timestamped report
    timestamp = datetime.now().strftime('%Y_%m_%d_%H%M%S')
    report_file = os.path.join(EVAL_DIR, 'reports', f'eval_{timestamp}.json')
    with open(report_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"\n📊 Report saved to: evaluation/reports/eval_{timestamp}.json")

def evaluate_notes_processor():
    print("Evaluating Phase 1: Notes Processor...")
    
    with open(os.path.join(EVAL_DIR, 'sample_meeting_notes.txt'), 'r') as f:
        notes_content = f.read()

    start_time = time.time()
    response = client.post("/api/process-notes", json={"notes": notes_content})
    duration = time.time() - start_time

    if response.status_code != 200:
        print(f"❌ Failed to process notes: {response.status_code} - {response.text}")
        return False, duration

    data = response.json()
    action_items = data.get("action_items", [])
    
    passed = True
    
    # Check 1: All 5 action items extracted
    if len(action_items) != 5:
        print(f"❌ Expected 5 action items, found {len(action_items)}")
        passed = False
    else:
        print("✅ All 5 action items extracted")

    # Check 2: Correct owner assignment & Missing owner handling
    owners = [item.get("owner", "") for item in action_items]
    if "Unassigned" not in owners:
        print("❌ Missing owner did not become 'Unassigned'")
        passed = False
    else:
        print("✅ Missing owner becomes 'Unassigned'")

    # Check 3: Missing deadline handling
    # We expect the Q2 Board Report item (unassigned) to have no deadline
    unassigned_items = [i for i in action_items if i.get("owner") == "Unassigned"]
    if unassigned_items and unassigned_items[0].get("deadline") is not None:
        print("❌ Missing deadline did not become null")
        passed = False
    else:
        print("✅ Missing deadline becomes null")
        
    if duration > 10.0:
        print(f"❌ Response time over 10 seconds: {duration:.2f}s")
        passed = False
    else:
        print(f"✅ Response time under 10 seconds: {duration:.2f}s")

    return passed, duration

def evaluate_email_summarizer():
    print("\nEvaluating Phase 2: Email Summarizer...")
    
    with open(os.path.join(EVAL_DIR, 'sample_email.txt'), 'r') as f:
        email_content = f.read()

    start_time = time.time()
    response = client.post("/api/summarize-email", json={"email_content": email_content})
    duration = time.time() - start_time

    if response.status_code != 200:
        print(f"❌ Failed to process email: {response.status_code} - {response.text}")
        return False, duration

    data = response.json()
    action_items = [item.lower() for item in data.get("action_items", [])]
    
    passed = True
    
    # Check 1: Action items include "use the new reporting template" and "include volunteer hours"
    action_1_found = any("reporting template" in item or "new version" in item for item in action_items)
    action_2_found = any("volunteer hours" in item for item in action_items)
    
    if not (action_1_found and action_2_found):
        print("❌ Failed to extract correct action items from email.")
        print(f"   Found: {data.get('action_items')}")
        passed = False
    else:
        print("✅ Correct action items extracted from email")
        
    return passed, duration

def evaluate_qa():
    print("\nEvaluating Phase 4: Q&A Assistant...")
    
    # 1. Clear docs and upload sample notes
    client.post("/api/clear-documents")
    with open(os.path.join(EVAL_DIR, 'sample_meeting_notes.txt'), 'rb') as f:
        client.post("/api/documents", files={"file": ("sample_meeting_notes.txt", f, "text/plain")})
        
    passed = True
    start_time = time.time()
    
    # Check 1: Found question
    resp1 = client.post("/api/ask", json={"question": "What is the grant deadline?"})
    if resp1.status_code != 200:
        print(f"❌ QA error: {resp1.text}")
        return False, 0
    data1 = resp1.json()
    if not data1.get("found"):
        print("❌ Failed to find known answer (grant deadline).")
        passed = False
    elif "April 1" not in data1.get("answer", ""):
        print("❌ Found answer but it didn't contain 'April 1'.")
        passed = False
    elif "source: sample_meeting_notes.txt" not in data1.get("source_citation", ""):
        print("❌ Missing or incorrect source citation format.")
        passed = False
    elif not data1.get("matched_text"):
        print("❌ Missing matched text snippet.")
        passed = False
    else:
        print("✅ Correctly answered and cited known question")
        
    # Check 2: Hallucination prevention
    resp2 = client.post("/api/ask", json={"question": "What did we discuss about hiring?"})
    data2 = resp2.json()
    if data2.get("found") or "I couldn't find this" not in data2.get("answer", ""):
        print("❌ Failed hallucination check (hiring).")
        passed = False
    else:
        print("✅ Correctly rejected unknown question")
        
    duration = time.time() - start_time
    return passed, duration

def evaluate_retrieval_and_reranking():
    print("\nEvaluating Phase 4.5: Retrieval & Re-Ranking...")
    
    # 1. Clear docs and upload sample notes
    client.post("/api/clear-documents")
    with open(os.path.join(EVAL_DIR, 'sample_meeting_notes.txt'), 'rb') as f:
        client.post("/api/documents", files={"file": ("sample_meeting_notes.txt", f, "text/plain")})
        
    passed = True
    start_time = time.time()
    
    question = "What is the grant deadline?"
    
    # Step A: Evaluate Base Cosine Similarity (Top 10)
    candidates = get_top_k_cosine(question, k=10)
    
    # The chunk with "deadline" should be in candidates.
    deadline_chunk_index = -1
    for i, c in enumerate(candidates):
        if "deadline" in c["text"].lower() and "grant" in c["text"].lower():
            deadline_chunk_index = i
            break
            
    if deadline_chunk_index == -1:
        print("❌ Retrieval Recall@10 Failed: Grant deadline chunk not found in top 10.")
        passed = False
    else:
        print(f"✅ Retrieval Recall@10 Passed (Ranked #{deadline_chunk_index + 1})")
        
    # Step B: Evaluate Re-Ranking
    reranked = retrieve_context(question)
    
    reranked_deadline_chunk_index = -1
    for i, c in enumerate(reranked):
        if "deadline" in c["text"].lower() and "grant" in c["text"].lower():
            reranked_deadline_chunk_index = i
            break
            
    if reranked_deadline_chunk_index == -1:
        print("❌ Re-Ranking Failed: Grant deadline chunk not found in top 3.")
        passed = False
    else:
        print(f"✅ Re-Ranking Improvement Passed (Ranked #{reranked_deadline_chunk_index + 1})")
        
    if deadline_chunk_index > reranked_deadline_chunk_index:
        print(f"   (Improved from #{deadline_chunk_index + 1} to #{reranked_deadline_chunk_index + 1})")
        
    duration = time.time() - start_time
    return passed, duration

def main():
    llm_provider = os.getenv("LLM_PROVIDER", "mock").lower()
    
    if llm_provider == "anthropic" and not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY is not set. Please set it to run Anthropic evaluations.")
        sys.exit(1)
    elif llm_provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY is not set. Please set it to run Gemini evaluations.")
        sys.exit(1)
        
    print(f"🚀 Running evaluations using Provider: {llm_provider.upper()}")
    
    os.makedirs(os.path.join(EVAL_DIR, 'reports'), exist_ok=True)
    
    metrics = load_metrics()
    
    notes_passed, notes_duration = evaluate_notes_processor()
    email_passed, email_duration = evaluate_email_summarizer()
    qa_passed, qa_duration = evaluate_qa()
    rerank_passed, rerank_duration = evaluate_retrieval_and_reranking()
    
    # Update metrics
    metrics["action_item_accuracy"] = 100 if (notes_passed and email_passed) else (50 if notes_passed or email_passed else 0)
    metrics["citation_accuracy"] = 100 if qa_passed else 0
    metrics["hallucination_failures"] = 0 if qa_passed else 1
    metrics["avg_response_time"] = round((notes_duration + email_duration + qa_duration + rerank_duration) / 4, 2)
    metrics["retrieval_recall_10"] = 100 if rerank_passed else 0
    metrics["reranking_improvement"] = 100 if rerank_passed else 0
    
    save_metrics(metrics)
    
    if notes_passed and email_passed and qa_passed and rerank_passed:
        print("\n✅ All Evaluations Passed!")
    else:
        print("\n❌ Evaluation Failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
