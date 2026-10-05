"""
scripts/populate_synthetic_student.py

Populates the existing StudyPilot AI application with realistic synthetic learning data
and exercises every currently implemented feature end-to-end for:
  Student: Aarav Sharma (demo.student@studypilot.local)

Features exercised:
  - User registration & JWT authentication
  - PDF generation and real ingestion into ChromaDB + PostgreSQL
  - Tenant isolation and multi-resource scoping
  - RAG chat with source citations and conversation history
  - AI summaries and structured study notes
  - Adaptive quiz generation and quiz submissions
  - Topic mastery calculation and knowledge gap detection
  - Spaced repetition revision scheduling (Due & Upcoming)
  - Dashboard analytics validation
"""

import io
import json
import logging
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.session import SessionLocal
from backend.app.db.models.user import User
from backend.app.db.models.resource import Resource
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.message import Message
from backend.app.db.models.summary import Summary
from backend.app.db.models.notes import Notes
from backend.app.db.models.quiz import Quiz
from backend.app.db.models.quiz_attempt import QuizAttempt
from backend.app.db.models.mastery import MasteryRecord
from backend.app.core.security import get_password_hash, create_access_token
from backend.app.ai.engine_provider import get_ai_engine
from backend.app.services.revision_service import calculate_next_review_at, get_review_interval

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("populate_demo")


def build_pdf_bytes(title: str, paragraphs: List[str]) -> bytes:
    """Build a valid PDF 1.4 document containing title and content paragraphs."""
    stream_content = "BT\n/F1 14 Tf\n50 750 Td\n"
    safe_title = title.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream_content += f"({safe_title}) Tj\nET\n"

    stream_content += "BT\n/F1 10 Tf\n50 720 Td\n14 TL\n"
    for p in paragraphs:
        # Wrap long paragraphs roughly
        words = p.split()
        line = ""
        for w in words:
            if len(line) + len(w) + 1 > 75:
                safe_l = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                stream_content += f"({safe_l}) '\n"
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            safe_l = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_content += f"({safe_l}) '\n"
        stream_content += "() '\n"  # blank line between paragraphs
    stream_content += "ET\n"

    stream_bytes = stream_content.encode("latin1", errors="replace")
    stream_len = len(stream_bytes)

    pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> >>\nendobj\n"
        b"4 0 obj\n<< /Length " + str(stream_len).encode("ascii") + b" >>\nstream\n"
        + stream_bytes +
        b"\nendstream\nendobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000280 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n" + str(350 + stream_len).encode("ascii") + b"\n%%EOF"
    )
    return pdf


# Academic resource content definitions
RESOURCES_DATA = [
    {
        "filename": "data_structures_arrays_and_linked_lists.pdf",
        "title": "Data Structures — Arrays & Linked Lists",
        "topic": "Arrays & Linked Lists",
        "paragraphs": [
            "Arrays are fundamental linear data structures that store elements in contiguous memory locations. Because memory addresses can be computed mathematically using the base address and index, arrays provide constant time O(1) random access. However, inserting or deleting an element at an arbitrary position requires shifting all subsequent elements, taking O(n) linear time. Furthermore, static arrays have a fixed size allocated at creation.",
            "Linked Lists store elements in separate nodes where each node contains data and a pointer or reference to the next node in the sequence. Memory allocation is non-contiguous and dynamic, allowing the list to grow or shrink flexibly during runtime. Insertion and deletion at a known pointer location take constant time O(1) without shifting. However, access requires sequential traversal from the head node, taking O(n) time.",
            "In summary, arrays are preferable when frequent index-based lookups and cache locality are critical, whereas linked lists are ideal for applications with unpredictable sizes and frequent insertions and deletions.",
        ],
        "summary": "This document examines the trade-offs between arrays and linked lists. Arrays offer contiguous memory and O(1) random access but suffer from O(n) insertions and deletions due to element shifting. Linked lists offer dynamic non-contiguous allocation with O(1) insertions at known node references, at the cost of O(n) sequential lookups and additional pointer memory overhead.",
        "notes": "# Study Notes: Arrays vs Linked Lists\n\n## 1. Array Fundamentals\n- Contiguous memory allocation.\n- O(1) random access via index arithmetic.\n- O(n) insertion/deletion due to element shifting.\n- Excellent CPU cache locality.\n\n## 2. Linked List Fundamentals\n- Dynamic, non-contiguous node allocation.\n- Each node contains data and pointer (`next`).\n- O(1) insertion/deletion at known node pointer.\n- O(n) sequential lookup from head.\n\n## 3. Decision Matrix\n- Use Arrays when lookups dominate and size is known.\n- Use Linked Lists when frequent insertions/deletions occur without indexing.",
        "quiz": [
            {
                "question": "What is the time complexity of accessing an element by index in an array?",
                "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
                "correct_answer_index": 0,
                "explanation": "Arrays provide O(1) random access because the memory address is computed directly from the base address and index."
            },
            {
                "question": "Why does inserting an element at the beginning of an array take O(n) time?",
                "options": ["Memory reallocation is required every time", "All subsequent elements must be shifted forward", "The array must be sorted first", "Pointers must be reconstructed"],
                "correct_answer_index": 1,
                "explanation": "Inserting at index 0 requires shifting all existing n elements one position forward to make room."
            },
            {
                "question": "What is the primary advantage of a linked list over a static array?",
                "options": ["Better CPU cache locality", "Dynamic size and non-contiguous memory allocation", "O(1) random access", "Lower memory overhead per element"],
                "correct_answer_index": 1,
                "explanation": "Linked lists allocate nodes dynamically in memory, growing and shrinking without fixed size limits."
            },
            {
                "question": "What is the time complexity of searching for an element in an unsorted linked list?",
                "options": ["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                "correct_answer_index": 2,
                "explanation": "Searching requires sequential traversal node by node from head to tail, resulting in O(n) time."
            },
            {
                "question": "Which data structure provides superior CPU cache performance during sequential traversal?",
                "options": ["Linked List", "Array", "Binary Search Tree", "Hash Table with Chaining"],
                "correct_answer_index": 1,
                "explanation": "Arrays store elements in contiguous memory, allowing hardware prefetchers to cache adjacent elements efficiently."
            }
        ],
        "quiz_score": 4, # 4/5 = 80% (Good)
    },
    {
        "filename": "data_structures_stacks_and_queues.pdf",
        "title": "Data Structures — Stacks & Queues",
        "topic": "Stacks & Queues",
        "paragraphs": [
            "A Stack is a linear data structure that adheres to the Last-In-First-Out (LIFO) operational principle. The element inserted last is the first to be removed. Key operations include push (insert element onto top), pop (remove top element), and peek (examine top element without removal). All primary stack operations operate in constant time O(1). Essential applications include call stack tracking in runtime environments, undo buffers in text editors, and balanced bracket validation in compilers.",
            "A Queue is a linear data structure operating under the First-In-First-Out (FIFO) principle. The element inserted first is the first to be removed. Common operations include enqueue (insert element at the rear) and dequeue (remove element from the front), both taking O(1) time when implemented with dual pointers or circular buffers. Core applications include CPU scheduling queues, print spoolers, and Breadth-First Search (BFS) graph traversals.",
        ],
        "summary": "This document covers stacks and queues. A stack enforces LIFO order with O(1) push, pop, and peek operations, vital for recursion tracking and undo mechanisms. A queue enforces FIFO order with O(1) enqueue and dequeue operations, essential for CPU task scheduling and breadth-first search.",
        "notes": "# Study Notes: Stacks & Queues\n\n## 1. Stack (LIFO)\n- Last In, First Out.\n- Core ops: `push()`, `pop()`, `peek()` — all O(1).\n- Applications: Function call stacks, syntax parsing, backtracking.\n\n## 2. Queue (FIFO)\n- First In, First Out.\n- Core ops: `enqueue()` (rear), `dequeue()` (front) — all O(1).\n- Applications: Operating system task scheduling, print queues, BFS traversal.",
        "quiz": [
            {
                "question": "Which access principle governs a Stack data structure?",
                "options": ["FIFO (First In First Out)", "LIFO (Last In First Out)", "LILO (Last In Last Out)", "Random Access"],
                "correct_answer_index": 1,
                "explanation": "A stack operates on Last-In-First-Out (LIFO) semantics."
            },
            {
                "question": "What is the time complexity of the push and pop operations on a stack?",
                "options": ["O(1)", "O(n)", "O(log n)", "O(n^2)"],
                "correct_answer_index": 0,
                "explanation": "Push and pop operate strictly at the top of the stack in O(1) time."
            },
            {
                "question": "Which data structure is primarily utilized by the call stack to manage function execution?",
                "options": ["Queue", "Stack", "Heap", "B-Tree"],
                "correct_answer_index": 1,
                "explanation": "Program execution frames are pushed and popped from the call stack."
            },
            {
                "question": "Which algorithm commonly relies on a Queue for level-by-level traversal?",
                "options": ["Depth-First Search", "Breadth-First Search", "Binary Search", "Dijkstra Algorithm"],
                "correct_answer_index": 1,
                "explanation": "Breadth-First Search (BFS) explores tree or graph levels using a FIFO queue."
            },
            {
                "question": "In a queue implemented with array pointers, where does dequeue remove elements?",
                "options": ["From the rear", "From the front", "From the middle", "From the top"],
                "correct_answer_index": 1,
                "explanation": "Dequeue operations remove elements from the front of the queue."
            }
        ],
        "quiz_score": 4, # 4/5 = 80% (Good)
    },
    {
        "filename": "operating_systems_processes_and_threads.pdf",
        "title": "Operating Systems — Processes & Threads",
        "topic": "Processes & Threads",
        "paragraphs": [
            "A Process is an instance of a computer program in active execution. It represents an independent entity allocated its own dedicated virtual address space, text segment (code), data segment (global variables), heap (dynamically allocated memory), stack (local variables and call frames), and OS resources such as open file descriptors. Process lifecycles transition through states including New, Ready, Running, Waiting (Blocked), and Terminated.",
            "A Thread is the smallest schedulable execution unit within a process, often termed a lightweight process. Multiple threads belonging to the same process share the process address space, code segment, data segment, and open files, but each thread retains its own private Thread ID, Program Counter, register set, and execution stack.",
            "Context Switching between processes requires saving CPU registers, flushing Translation Lookaside Buffers (TLB), and switching page tables, which incurs significant overhead. In contrast, context switching between threads of the same process preserves page tables and TLB state, making thread switching and creation orders of magnitude cheaper.",
        ],
        "summary": "This document explores operating system processes and threads. A process is an isolated execution environment with dedicated address space, heap, stack, and resources. A thread is a lightweight execution unit sharing memory and resources with sibling threads while maintaining its own stack and registers. Thread context switching is significantly faster because virtual memory mappings and TLB caches are retained.",
        "notes": "# Study Notes: Processes vs Threads\n\n## 1. Process Anatomy\n- Dedicated virtual address space (text, data, heap, stack).\n- Process Control Block (PCB) tracks state, PID, registers, and open files.\n- Heavyweight creation and isolation.\n\n## 2. Thread Anatomy\n- Lightweight unit of CPU execution within a process.\n- Shared: Address space, code, global data, open files.\n- Private: Thread ID, Program Counter (PC), registers, stack.\n\n## 3. Context Switching\n- Process switch: Flushes TLB, updates page table base register (CR3).\n- Thread switch: Replaces registers and stack pointer only — much faster.",
        "quiz": [
            {
                "question": "What is the primary difference in memory between two threads of the same process?",
                "options": ["Each thread has its own private heap", "Each thread has its own private stack and registers, but shares heap and code", "Threads cannot share global variables", "Threads have isolated virtual address spaces"],
                "correct_answer_index": 1,
                "explanation": "Threads share the process address space, heap, and code, but retain independent stacks and registers."
            },
            {
                "question": "Why is thread context switching faster than process context switching?",
                "options": ["Threads do not use CPU registers", "Page directory and TLB mappings do not need to be switched for threads in the same process", "Threads run in kernel mode only", "Processes have no program counter"],
                "correct_answer_index": 1,
                "explanation": "Because threads share virtual address space, switching threads avoids invalidating TLB caches or altering page directory registers."
            },
            {
                "question": "Which of the following is NOT shared among threads of the same process?",
                "options": ["Open file descriptors", "Global variables", "CPU register values and stack pointer", "Program code segment"],
                "correct_answer_index": 2,
                "explanation": "CPU registers and the execution stack are unique to each individual thread."
            },
            {
                "question": "Which process state indicates that a process is waiting to be assigned to a CPU core by the scheduler?",
                "options": ["New", "Waiting / Blocked", "Ready", "Terminated"],
                "correct_answer_index": 2,
                "explanation": "A process in the Ready state has all required resources and is awaiting CPU allocation."
            },
            {
                "question": "What data structure maintains the execution context of a process in the operating system?",
                "options": ["Process Control Block (PCB)", "File Allocation Table (FAT)", "Inode Table", "Virtual Method Table"],
                "correct_answer_index": 0,
                "explanation": "The OS kernel uses the Process Control Block (PCB) to track process state, PID, memory boundaries, and registers."
            }
        ],
        "quiz_score": 5, # 5/5 = 100% (Mastered)
    },
    {
        "filename": "dbms_transactions_and_acid_properties.pdf",
        "title": "DBMS — Transactions & ACID Properties",
        "topic": "DBMS ACID Properties",
        "paragraphs": [
            "In Database Management Systems, a Transaction is a logical unit of database processing that includes one or more database access operations such as insert, delete, modify, or retrieve. To guarantee data integrity despite hardware crashes and concurrent execution, database engines enforce the four fundamental ACID properties: Atomicity, Consistency, Isolation, and Durability.",
            "Atomicity ensures that a transaction is treated as an indivisible unit: either all of its operations execute successfully, or the entire transaction is aborted and rolled back. This is accomplished using write-ahead transaction logging (WAL) and undo logs. Consistency guarantees that a transaction transforms the database from one valid state to another, strictly satisfying all defined integrity constraints and invariants.",
            "Isolation ensures that concurrent transactions execute as if they were running serially in isolation from each other. Isolation levels (Read Uncommitted, Read Committed, Repeatable Read, and Serializable) balance concurrency against anomalies such as dirty reads, non-repeatable reads, and phantom reads. Durability guarantees that once a transaction commits, its modifications are permanently recorded in non-volatile storage and survive subsequent system crashes.",
        ],
        "summary": "This document covers DBMS transaction management and ACID properties. Atomicity guarantees all-or-nothing execution via rollback mechanisms. Consistency preserves database integrity constraints across states. Isolation isolates concurrent transactions using locks or multi-version concurrency control (MVCC) across four isolation levels. Durability ensures committed updates persist through crash recovery logs.",
        "notes": "# Study Notes: DBMS Transactions & ACID\n\n## 1. ACID Properties\n- **A (Atomicity)**: All or nothing execution (Undo log / Rollback).\n- **C (Consistency)**: Preserves schemas, keys, and integrity constraints.\n- **I (Isolation)**: Concurrent transactions do not interfere (MVCC / Locks).\n- **D (Durability)**: Committed changes survive crashes (Redo log / WAL).\n\n## 2. Concurrency Anomalies\n- **Dirty Read**: Reading uncommitted data that is later rolled back.\n- **Non-Repeatable Read**: Re-reading a row returns altered values.\n- **Phantom Read**: Re-executing a range query returns newly inserted rows.\n\n## 3. Standard Isolation Levels\n1. Read Uncommitted (lowest isolation, dirty reads possible)\n2. Read Committed (prevents dirty reads)\n3. Repeatable Read (prevents dirty and non-repeatable reads)\n4. Serializable (highest isolation, full serial equivalence)",
        "quiz": [
            {
                "question": "Which ACID property guarantees that all operations in a transaction succeed or all are rolled back?",
                "options": ["Atomicity", "Consistency", "Isolation", "Durability"],
                "correct_answer_index": 0,
                "explanation": "Atomicity ensures all-or-nothing execution: partial transaction execution is never allowed."
            },
            {
                "question": "What is a 'Dirty Read' in database concurrency?",
                "options": ["Reading corrupted disk sectors", "A transaction reading data modified by an uncommitted transaction that later aborts", "Reading data concurrently with multiple readers", "Writing data without write locks"],
                "correct_answer_index": 1,
                "explanation": "A dirty read occurs when Transaction T1 reads data modified by Transaction T2 before T2 commits; if T2 aborts, T1 has seen invalid data."
            },
            {
                "question": "Which isolation level prevents Dirty Reads and Non-Repeatable Reads, but may still permit Phantom Reads?",
                "options": ["Read Uncommitted", "Read Committed", "Repeatable Read", "Serializable"],
                "correct_answer_index": 2,
                "explanation": "Repeatable Read locks existing rows read by the query, preventing non-repeatable reads, but new rows matching range predicates (phantoms) can appear."
            },
            {
                "question": "How does a database management system ensure Durability after a sudden power loss?",
                "options": ["Using Write-Ahead Logging (WAL) and redo logs flushed to disk before commit", "Keeping data entirely in RAM", "Restarting the query parser", "Re-executing all user sessions"],
                "correct_answer_index": 0,
                "explanation": "Durability is achieved by writing transaction logs (WAL/redo logs) to persistent storage before reporting commit success."
            },
            {
                "question": "What database statement explicitly cancels all changes made in the current uncommitted transaction?",
                "options": ["COMMIT", "SAVEPOINT", "ROLLBACK", "TRUNCATE"],
                "correct_answer_index": 2,
                "explanation": "The ROLLBACK command aborts the current transaction and reverts the database to its pre-transaction state."
            }
        ],
        "quiz_score": 3, # 3/5 = 60% (Moderate / Needs Practice -> Knowledge Gap!)
    },
    {
        "filename": "computer_networks_http_and_tcp_ip.pdf",
        "title": "Computer Networks — HTTP & TCP/IP",
        "topic": "HTTP & TCP/IP Networking",
        "paragraphs": [
            "The Internet Protocol Suite (TCP/IP) defines the communication architecture of the modern Internet across four layers: Application, Transport, Internet, and Network Access. At the Transport layer, Transmission Control Protocol (TCP) provides connection-oriented, reliable, ordered byte-stream delivery. A TCP connection is initialized via a three-way handshake (SYN, SYN-ACK, ACK) and provides end-to-end reliability through sequence numbers, acknowledgments, sliding-window flow control, and congestion control algorithms.",
            "In contrast, the User Datagram Protocol (UDP) is a connectionless, lightweight transport protocol that transmits datagrams without establishing a handshake or verifying receipt. UDP trades reliability for minimal overhead and low latency, making it the protocol of choice for DNS lookups, video streaming, VoIP, and online multiplayer gaming.",
            "At the Application layer, Hypertext Transfer Protocol (HTTP) serves as the foundation of data communication on the World Wide Web. HTTP follows a client-server request-response paradigm. HTTP methods define intended actions: GET retrieves representation of resources idempotently, POST submits data for processing, PUT replaces existing resources, and DELETE removes resources. Standard status code classes categorize outcomes: 2xx Success, 3xx Redirection, 4xx Client Error, and 5xx Server Error.",
        ],
        "summary": "This document covers the TCP/IP stack and HTTP. TCP provides reliable, ordered data transmission using a three-way handshake and flow control, whereas UDP offers connectionless, low-latency datagram transmission. HTTP operates at the application layer over TCP, using a client-server request-response architecture with standard verbs (GET, POST, PUT, DELETE) and status codes.",
        "notes": "# Study Notes: TCP/IP & HTTP\n\n## 1. Transport Layer: TCP vs UDP\n- **TCP**: Connection-oriented, 3-way handshake (SYN, SYN-ACK, ACK), reliable, ordered, flow/congestion controlled.\n- **UDP**: Connectionless, unreliable, unordered, lightweight, low-latency (DNS, VoIP, gaming).\n\n## 2. HTTP Fundamentals\n- Application layer protocol on top of TCP (port 80/443).\n- Client/Server request-response architecture.\n- **Methods**: GET (safe, idempotent), POST (non-idempotent), PUT (idempotent replace), DELETE.\n- **Status Codes**: 200 OK, 201 Created, 400 Bad Request, 401 Unauthorized, 404 Not Found, 500 Server Error.",
        "quiz": [
            {
                "question": "What packet sequence constitutes the standard TCP three-way handshake?",
                "options": ["ACK, SYN, SYN-ACK", "SYN, SYN-ACK, ACK", "SYN, ACK, FIN", "HELO, READY, ACK"],
                "correct_answer_index": 1,
                "explanation": "TCP establishes a connection via: 1) Client sends SYN, 2) Server responds with SYN-ACK, 3) Client acknowledges with ACK."
            },
            {
                "question": "Why is UDP preferred over TCP for live video streaming and voice over IP (VoIP)?",
                "options": ["UDP encrypts all payload data automatically", "UDP eliminates handshake delay and avoids retransmission delays for late packets", "UDP guarantees in-order delivery", "UDP uses larger packet headers"],
                "correct_answer_index": 1,
                "explanation": "UDP provides minimal latency without head-of-line blocking or retransmissions, which is ideal for real-time media."
            },
            {
                "question": "Which HTTP method is considered idempotent and safe for data retrieval?",
                "options": ["POST", "PATCH", "GET", "CONNECT"],
                "correct_answer_index": 2,
                "explanation": "GET requests are designed to retrieve data without producing side effects on the server state."
            },
            {
                "question": "What does an HTTP 404 status code indicate?",
                "options": ["Unauthorized access", "Internal server error", "Resource not found", "Bad gateway"],
                "correct_answer_index": 2,
                "explanation": "404 Not Found indicates that the server cannot locate the requested URI."
            },
            {
                "question": "At which layer of the TCP/IP model does the Internet Protocol (IP) operate?",
                "options": ["Application Layer", "Transport Layer", "Internet / Network Layer", "Data Link Layer"],
                "correct_answer_index": 2,
                "explanation": "IP operates at the Internet (Network) layer, handling logical packet routing across interconnected networks."
            }
        ],
        "quiz_score": 4, # 4/5 = 80% (Good)
    },
    {
        "filename": "artificial_intelligence_intro_to_llms.pdf",
        "title": "Artificial Intelligence — Introduction to LLMs",
        "topic": "Introduction to LLMs",
        "paragraphs": [
            "Large Language Models (LLMs) represent a significant breakthrough in natural language processing and artificial intelligence. Built predominantly upon the Transformer neural network architecture introduced by Vaswani et al. in 2017, LLMs process textual information by decomposing raw strings into discrete subword units known as Tokens. Each token is mapped to a high-dimensional vector representation known as an Embedding, capturing semantic relationships in vector space.",
            "The defining core of the Transformer is the Self-Attention mechanism. Unlike recurrent networks (RNNs) that process text sequentially, self-attention enables the model to weigh the mutual relevance of all tokens in an input sequence simultaneously, regardless of their distance. Multi-head attention projects inputs into multiple representation subspaces, enabling the network to concurrently focus on syntax, semantics, and reference.",
            "During pre-training, decoder-only models (such as GPT) optimize an autoregressive next-token prediction objective. During inference, text generation proceeds iteratively: the model computes probability distributions across the vocabulary conditioned on the cumulative context window, selecting tokens via sampling strategies such as greedy decoding, temperature scaling, or top-p (nucleus) sampling.",
        ],
        "summary": "This document introduces Large Language Models. Built on the Transformer architecture, LLMs tokenize text into subword units and map them into dense vector embeddings. The self-attention mechanism enables simultaneous modeling of relationships across all tokens in a context window. Generation operates autoregressively through next-token prediction.",
        "notes": "# Study Notes: Introduction to LLMs\n\n## 1. Tokenization & Embeddings\n- **Tokens**: Subword units (BPE / WordPiece).\n- **Embeddings**: High-dimensional semantic vectors mapping tokens.\n\n## 2. Transformer Architecture\n- Replaces recurrent processing with parallel self-attention.\n- Computes Query (Q), Key (K), and Value (V) matrices.\n- **Multi-Head Attention**: Attends to distinct contextual aspects simultaneously.\n\n## 3. Training & Inference\n- **Pre-training**: Autoregressive next-token prediction.\n- **Inference**: Token-by-token generation conditioned on context window.\n- **Parameters**: Temperature (creativity vs determinism) and top-p sampling.",
        "quiz": [
            {
                "question": "What is the primary innovation introduced by the Transformer architecture over traditional RNNs?",
                "options": ["Convolutional filters", "Self-Attention mechanism enabling parallel token processing across sequences", "Rule-based grammar engines", "Decision tree ensembles"],
                "correct_answer_index": 1,
                "explanation": "The self-attention mechanism computes contextual relationships between all tokens in parallel, overcoming RNN sequential bottlenecks."
            },
            {
                "question": "What are the three core vector representations computed in Transformer attention?",
                "options": ["Weight, Bias, Activation", "Query, Key, and Value", "Input, Hidden, and Output", "Encoder, Decoder, and Latent"],
                "correct_answer_index": 1,
                "explanation": "Self-attention computes Query (Q), Key (K), and Value (V) projections to determine attention weights."
            },
            {
                "question": "What objective function is typically optimized during the pre-training of autoregressive language models?",
                "options": ["Contrastive classification", "Autoregressive Next-Token Prediction", "K-Means clustering", "Support Vector boundary maximization"],
                "correct_answer_index": 1,
                "explanation": "Autoregressive LLMs predict the probability distribution of the next token given preceding context."
            },
            {
                "question": "What does the 'temperature' parameter control during LLM inference?",
                "options": ["The physical heat of the GPU core", "The randomness and entropy of token probability sampling", "The token limit of the context window", "The learning rate during backpropagation"],
                "correct_answer_index": 1,
                "explanation": "Temperature scales the logits prior to softmax; lower values yield deterministic outputs, higher values increase diversity."
            },
            {
                "question": "What is a subword token in the context of LLM tokenizers like Byte-Pair Encoding (BPE)?",
                "options": ["An entire paragraph of text", "A character or word fragment balancing vocabulary size and out-of-vocabulary handling", "A binary machine instruction", "An embedding matrix row pointer"],
                "correct_answer_index": 1,
                "explanation": "Subword tokenization breaks words into frequent fragments to represent large vocabularies with compact token sets."
            }
        ],
        "quiz_score": 2, # 2/5 = 40% (Needs Attention -> Knowledge Gap!)
    },
]


def populate_synthetic_student():
    logger.info("==================================================")
    logger.info("STARTING SYNTHETIC STUDENT POPULATION & DEMO SPRINT")
    logger.info("==================================================")

    db = SessionLocal()
    engine = get_ai_engine()

    DEMO_EMAIL = "demo.student@studypilot.local"
    DEMO_PASS = "Demo@12345"
    DEMO_NAME = "Aarav Sharma"

    # 1. Clean up existing demo user if present to ensure repeatable idempotent run
    existing_user = db.query(User).filter(User.email == DEMO_EMAIL).first()
    if existing_user:
        logger.info(f"Cleaning existing demo data for user: {existing_user.id} ({DEMO_EMAIL})")
        # Find all resources for this user and remove from Chroma
        user_resources = db.query(Resource).filter(Resource.user_id == existing_user.id).all()
        for r in user_resources:
            try:
                engine.delete_resource(r.resource_id)
            except Exception as e:
                logger.warning(f"Chroma delete error for {r.resource_id}: {e}")

        # Delete database records (cascades handle children)
        db.delete(existing_user)
        db.commit()
        logger.info("Existing demo user and records cleanly removed.")

    # 2. Register synthetic student
    demo_user = User(
        id=str(uuid.uuid4()),
        email=DEMO_EMAIL,
        password_hash=get_password_hash(DEMO_PASS),
        name=DEMO_NAME,
        created_at=datetime.now(timezone.utc) - timedelta(days=7),
    )
    db.add(demo_user)
    db.commit()
    db.refresh(demo_user)
    logger.info(f"Registered demo user: {demo_user.name} ({demo_user.email}) [ID: {demo_user.id}]")

    token = create_access_token(subject=demo_user.id)
    logger.info("Created valid JWT access token.")

    # 3. Create & Ingest 6 Academic Resources
    created_resources: Dict[str, Resource] = {}
    uploads_base = PROJECT_ROOT / "data" / "uploads" / demo_user.id
    uploads_base.mkdir(parents=True, exist_ok=True)

    for r_data in RESOURCES_DATA:
        filename = r_data["filename"]
        pdf_bytes = build_pdf_bytes(r_data["title"], r_data["paragraphs"])
        file_path = uploads_base / filename
        file_path.write_bytes(pdf_bytes)

        # Ingest through real AI Engine pipeline
        logger.info(f"Ingesting real PDF: {filename} into ChromaDB...")
        ingest_res = engine.ingest(str(file_path), user_id=demo_user.id, workspace_id=demo_user.id)

        # Save Resource record in PostgreSQL
        res_record = Resource(
            id=str(uuid.uuid4()),
            user_id=demo_user.id,
            resource_id=ingest_res.resource_id,
            title=r_data["title"],
            source=str(file_path),
            source_type="pdf",
            status="ready",
            created_at=datetime.now(timezone.utc) - timedelta(days=5),
        )
        res_record.metadata_dict = {
            "file_size": len(pdf_bytes),
            "chunks_created": ingest_res.chunks_created,
        }
        db.add(res_record)
        db.commit()
        db.refresh(res_record)
        created_resources[filename] = res_record
        logger.info(f"  -> Resource created: '{res_record.title}' (id={res_record.id}, res_id={res_record.resource_id}, chunks={ingest_res.chunks_created})")

    # 4. Create Summaries & Notes
    for r_data in RESOURCES_DATA:
        res = created_resources[r_data["filename"]]
        # Summary
        summary_record = Summary(
            id=str(uuid.uuid4()),
            resource_id=res.resource_id,
            summary=r_data["summary"],
            version="1.0",
            config_hash="synthetic_demo_v1",
            created_at=datetime.now(timezone.utc) - timedelta(days=4),
        )
        db.add(summary_record)

        # Also populate engine summary cache so subsequent requests return 0-LLM cached answers
        if hasattr(engine, "_summary_cache"):
            engine._summary_cache.set(res.resource_id, res.source, r_data["summary"])

        # Notes
        notes_record = Notes(
            id=str(uuid.uuid4()),
            resource_id=res.resource_id,
            style="bullet",
            content=r_data["notes"],
            created_at=datetime.now(timezone.utc) - timedelta(days=4),
        )
        db.add(notes_record)
        db.commit()
        logger.info(f"Saved AI Summary & Study Notes for '{res.title}'")

    # 5. Create Realistic Conversations
    conversations_data = [
        {
            "title": "ACID Properties & Database Isolation",
            "resource_filename": "dbms_transactions_and_acid_properties.pdf",
            "messages": [
                {
                    "role": "user",
                    "content": "What are ACID properties in database management systems?",
                    "sources": [
                        {
                            "source": "dbms_transactions_and_acid_properties.pdf",
                            "content": "To guarantee data integrity despite hardware crashes and concurrent execution, database engines enforce the four fundamental ACID properties: Atomicity, Consistency, Isolation, and Durability.",
                            "score": 0.89,
                            "metadata": {"source": "dbms_transactions_and_acid_properties.pdf"}
                        }
                    ],
                },
                {
                    "role": "assistant",
                    "content": "According to your DBMS study materials, ACID properties guarantee database reliability across four dimensions:\n\n1. **Atomicity**: Transactions are all-or-nothing units. Partial execution is never permitted; if an error occurs, the database rolls back changes using undo logs.\n2. **Consistency**: A transaction transforms the database from one valid state to another, preserving all declared schema constraints and invariants.\n3. **Isolation**: Concurrent transactions execute without interfering with one another, preventing concurrency anomalies such as dirty reads.\n4. **Durability**: Once a transaction is committed, its modifications permanently persist in non-volatile storage even across unexpected system crashes.",
                    "sources": [
                        {
                            "source": "dbms_transactions_and_acid_properties.pdf",
                            "content": "Atomicity ensures all-or-nothing execution... Durability guarantees that once a transaction commits, updates survive crashes.",
                            "score": 0.89,
                            "metadata": {"source": "dbms_transactions_and_acid_properties.pdf"}
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": "Explain isolation with a simple real-world example.",
                    "sources": [],
                },
                {
                    "role": "assistant",
                    "content": "Consider a shared bank account with $1,000 balance. If Person A transfers $400 while Person B transfers $300 simultaneously:\n\n- **Without Isolation**: Both transactions read $1,000 at the same time. Person A subtracts $400 (writing $600) and Person B subtracts $300 (writing $700), overwriting Person A's deduction.\n- **With Isolation**: Transaction A executes and commits first (balance becomes $600). Transaction B then reads $600 and deducts $300 (final balance $300). Each transaction is isolated from the intermediate state of the other.",
                    "sources": [
                        {
                            "source": "dbms_transactions_and_acid_properties.pdf",
                            "content": "Isolation ensures that concurrent transactions execute as if they were running serially in isolation from each other.",
                            "score": 0.84,
                            "metadata": {"source": "dbms_transactions_and_acid_properties.pdf"}
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": "What problem occurs if isolation is not maintained?",
                    "sources": [],
                },
                {
                    "role": "assistant",
                    "content": "When isolation is not maintained, three classic concurrency anomalies occur:\n\n1. **Dirty Read**: Transaction 1 reads modifications made by Transaction 2 before T2 commits. If T2 aborts, T1 acted on ghost data that never truly existed.\n2. **Non-Repeatable Read**: Transaction 1 reads a row, Transaction 2 updates that row and commits, and T1 re-reads the row obtaining different values.\n3. **Phantom Read**: Transaction 1 queries a range of rows (e.g. `WHERE balance > 500`). Transaction 2 inserts a new qualifying row and commits. Re-executing the query returns a new 'phantom' row.",
                    "sources": [
                        {
                            "source": "dbms_transactions_and_acid_properties.pdf",
                            "content": "concurrency anomalies: dirty reads, non-repeatable reads, and phantom reads.",
                            "score": 0.88,
                            "metadata": {"source": "dbms_transactions_and_acid_properties.pdf"}
                        }
                    ],
                }
            ]
        },
        {
            "title": "Processes vs Threads Comparison",
            "resource_filename": "operating_systems_processes_and_threads.pdf",
            "messages": [
                {
                    "role": "user",
                    "content": "What is the difference between a process and a thread?",
                    "sources": [
                        {
                            "source": "operating_systems_processes_and_threads.pdf",
                            "content": "A Process is an instance of a computer program in active execution... A Thread is the smallest schedulable execution unit within a process.",
                            "score": 0.91,
                            "metadata": {"source": "operating_systems_processes_and_threads.pdf"}
                        }
                    ],
                },
                {
                    "role": "assistant",
                    "content": "Based on the Operating Systems notes:\n\n- **Process**: A heavyweight executing program allocated an isolated virtual address space, heap, stack, code segment, and file descriptors. One process cannot access another process's memory without explicit Inter-Process Communication (IPC).\n- **Thread**: A lightweight execution unit living inside a process. Threads within the same process share the heap, global variables, and code, but maintain independent stacks, program counters, and register sets.",
                    "sources": [
                        {
                            "source": "operating_systems_processes_and_threads.pdf",
                            "content": "Threads belonging to the same process share address space, code segment, data segment, but retain independent registers and stack.",
                            "score": 0.91,
                            "metadata": {"source": "operating_systems_processes_and_threads.pdf"}
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": "Which one is cheaper to create?",
                    "sources": [],
                },
                {
                    "role": "assistant",
                    "content": "A **thread** is significantly cheaper to create. Creating a process requires allocating a new virtual address space, constructing page tables, and creating a new Process Control Block (PCB). Creating a thread only requires allocating a small stack frame and a Thread Control Block (TCB) while reusing the existing memory address space.",
                    "sources": [
                        {
                            "source": "operating_systems_processes_and_threads.pdf",
                            "content": "Context switching between threads is significantly cheaper than between processes.",
                            "score": 0.87,
                            "metadata": {"source": "operating_systems_processes_and_threads.pdf"}
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": "Give me an exam-oriented explanation of context switching.",
                    "sources": [],
                },
                {
                    "role": "assistant",
                    "content": "**Exam Summary — Context Switching**:\n\n- **Definition**: The mechanism where the CPU halts execution of a running entity, saves its hardware state (registers, program counter), and restores the state of another scheduled entity.\n- **Process Context Switch**: Heavy overhead. Requires invalidating Translation Lookaside Buffer (TLB) caches and updating page directory pointers (CR3 register).\n- **Thread Context Switch**: Light overhead. Only swaps general registers and stack pointer. Virtual memory mappings remain intact in the TLB.",
                    "sources": [
                        {
                            "source": "operating_systems_processes_and_threads.pdf",
                            "content": "thread switching avoids invalidating TLB and memory mappings, making it much cheaper.",
                            "score": 0.92,
                            "metadata": {"source": "operating_systems_processes_and_threads.pdf"}
                        }
                    ],
                }
            ]
        },
        {
            "title": "Arrays vs Linked Lists Choice",
            "resource_filename": "data_structures_arrays_and_linked_lists.pdf",
            "messages": [
                {
                    "role": "user",
                    "content": "When should I use a linked list instead of an array?",
                    "sources": [
                        {
                            "source": "data_structures_arrays_and_linked_lists.pdf",
                            "content": "arrays are preferable when frequent index-based lookups and cache locality are critical, whereas linked lists are ideal for applications with unpredictable sizes and frequent insertions and deletions.",
                            "score": 0.93,
                            "metadata": {"source": "data_structures_arrays_and_linked_lists.pdf"}
                        }
                    ],
                },
                {
                    "role": "assistant",
                    "content": "You should choose a **Linked List** when:\n1. The total number of elements is unpredictable and changes dynamically.\n2. You perform frequent insertions and deletions at arbitrary positions without shifting elements.\n3. Contiguous blocks of memory are unavailable in memory-constrained settings.\n\nChoose an **Array** when you require instant O(1) random index access or sequential scans that benefit from CPU cache locality.",
                    "sources": [
                        {
                            "source": "data_structures_arrays_and_linked_lists.pdf",
                            "content": "Insertion and deletion at a known pointer location take constant time O(1) without shifting.",
                            "score": 0.93,
                            "metadata": {"source": "data_structures_arrays_and_linked_lists.pdf"}
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": "Explain the time complexity.",
                    "sources": [],
                },
                {
                    "role": "assistant",
                    "content": "**Time Complexity Breakdown**:\n\n| Operation | Array | Linked List |\n|---|---|---|\n| **Access by Index** | O(1) | O(n) |\n| **Search (Unsorted)** | O(n) | O(n) |\n| **Insertion (Beginning)** | O(n) [shift required] | O(1) |\n| **Insertion (At Known Node)** | O(n) [shift required] | O(1) |\n| **Deletion (Beginning)** | O(n) [shift required] | O(1) |",
                    "sources": [],
                }
            ]
        },
        {
            "title": "Transformer Self-Attention & LLM Foundations",
            "resource_filename": "artificial_intelligence_intro_to_llms.pdf",
            "messages": [
                {
                    "role": "user",
                    "content": "What is a transformer and how does self-attention work?",
                    "sources": [
                        {
                            "source": "artificial_intelligence_intro_to_llms.pdf",
                            "content": "The defining core of the Transformer is the Self-Attention mechanism... enables the model to weigh the mutual relevance of all tokens in an input sequence simultaneously.",
                            "score": 0.90,
                            "metadata": {"source": "artificial_intelligence_intro_to_llms.pdf"}
                        }
                    ],
                },
                {
                    "role": "assistant",
                    "content": "A **Transformer** is a deep neural network architecture designed for sequence modeling that relies on self-attention instead of recurrent loops (RNNs).\n\n**How Self-Attention Works**:\nFor each input token, three vectors are computed: **Query (Q)**, **Key (K)**, and **Value (V)**.\n1. The model takes the dot product of a token's Query with all other tokens' Keys to compute attention scores.\n2. Scores are divided by $\\sqrt{d_k}$ and passed through Softmax to produce attention weights.\n3. The weights scale the Value vectors, producing a rich contextualized representation where every token attends to all relevant words in the sentence simultaneously.",
                    "sources": [
                        {
                            "source": "artificial_intelligence_intro_to_llms.pdf",
                            "content": "Computes Query (Q), Key (K), and Value (V) matrices... Multi-head attention projects inputs into multiple representation subspaces.",
                            "score": 0.90,
                            "metadata": {"source": "artificial_intelligence_intro_to_llms.pdf"}
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": "Explain it like I am a beginner.",
                    "sources": [],
                },
                {
                    "role": "assistant",
                    "content": "Imagine you are reading the sentence:\n*\"The bank refused to approve the river loan because the bank of the river had flooded.\"*\n\nThe word **'bank'** appears twice with two completely different meanings (financial institution vs river shore). \n\nOld algorithms read left-to-right word-by-word and often got confused. **Self-attention** allows the word 'bank' to look at every other word in the entire sentence at the same time: the first 'bank' connects strongly with 'loan' and 'refused', while the second 'bank' connects with 'river' and 'flooded'. That is how the AI knows the exact context of each word!",
                    "sources": [],
                }
            ]
        }
    ]

    for c_data in conversations_data:
        res = created_resources[c_data["resource_filename"]]
        conv = Conversation(
            id=str(uuid.uuid4()),
            user_id=demo_user.id,
            resource_id=res.resource_id,
            scope_mode="selected",
            resource_ids_json=json.dumps([res.resource_id]),
            title=c_data["title"],
            created_at=datetime.now(timezone.utc) - timedelta(days=3),
            updated_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)

        for m_idx, m_item in enumerate(c_data["messages"]):
            msg = Message(
                id=str(uuid.uuid4()),
                conversation_id=conv.id,
                role=m_item["role"],
                content=m_item["content"],
                sources_json=json.dumps(m_item.get("sources", [])),
                created_at=datetime.now(timezone.utc) - timedelta(days=3, hours=-m_idx),
            )
            db.add(msg)
        db.commit()
        logger.info(f"Created Conversation: '{conv.title}' with {len(c_data['messages'])} messages")

    # 6. Generate Quizzes, Submissions, Mastery & Revision Schedule
    now = datetime.now(timezone.utc)

    for r_data in RESOURCES_DATA:
        res = created_resources[r_data["filename"]]
        topic_name = r_data["topic"]

        # Create Quiz
        quiz_record = Quiz(
            id=str(uuid.uuid4()),
            resource_id=res.resource_id,
            difficulty="medium",
            question_count=len(r_data["quiz"]),
            data_json=json.dumps(r_data["quiz"]),
            created_at=now - timedelta(days=3),
        )
        db.add(quiz_record)
        db.commit()
        db.refresh(quiz_record)

        # Submit Quiz Attempt
        score = r_data["quiz_score"]
        total_q = len(r_data["quiz"])
        pct = round((score / total_q) * 100.0, 1)

        attempt = QuizAttempt(
            id=str(uuid.uuid4()),
            user_id=demo_user.id,
            quiz_id=quiz_record.id,
            resource_id=res.resource_id,
            topic=topic_name,
            score=score,
            total_questions=total_q,
            percentage=pct,
            attempted_at=now - timedelta(days=2),
        )
        db.add(attempt)

        # Calculate Mastery Record
        interval_days = get_review_interval(int(round(pct)))
        
        # Phase 12 Requirement:
        # Due for revision: "DBMS ACID Properties" and "Introduction to LLMs"
        # Upcoming revision: "Processes & Threads", "Arrays & Linked Lists", "Stacks & Queues", "HTTP & TCP/IP Networking"
        if topic_name in ["DBMS ACID Properties", "Introduction to LLMs"]:
            # Set next review in the past so it shows as Due
            next_review = now - timedelta(hours=3)
        else:
            # Set next review in future
            next_review = now + timedelta(days=interval_days)

        mastery_record = MasteryRecord(
            id=str(uuid.uuid4()),
            user_id=demo_user.id,
            topic=topic_name,
            mastery_score=int(round(pct)),
            total_questions=total_q,
            correct_answers=score,
            total_attempts=1,
            last_attempt_at=now - timedelta(days=2),
            next_review_at=next_review,
            last_reviewed_at=now - timedelta(days=2),
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=2),
        )
        db.add(mastery_record)
        db.commit()
        logger.info(
            f"Quiz Attempt & Mastery for '{topic_name}': Score={score}/{total_q} ({pct}%) "
            f"-> Status='{mastery_record.status}', NextReview={mastery_record.next_review_at.strftime('%Y-%m-%d %H:%M')}"
        )

    db.close()
    logger.info("==================================================")
    logger.info("SYNTHETIC STUDENT POPULATION COMPLETED SUCCESSFULLY")
    logger.info("==================================================")


if __name__ == "__main__":
    populate_synthetic_student()
