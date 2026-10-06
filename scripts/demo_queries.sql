-- ==============================================================================
-- STUDYPILOT AI — POSTGRESQL DEMO & LAB QUERIES
-- Database Name: studypilot
-- User: postgres
-- Usage: Run in pgAdmin Query Tool, psql, or VS Code SQL extension
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. TABLE OVERVIEW & ROW COUNTS (SAFE TO RUN ANYTIME)
-- ------------------------------------------------------------------------------

-- List all 9 business tables in the studypilot database
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Snapshot count of records across all major tables
SELECT 
  (SELECT count(*) FROM users) AS users_count,
  (SELECT count(*) FROM resources) AS resources_count,
  (SELECT count(*) FROM conversations) AS conversations_count,
  (SELECT count(*) FROM messages) AS messages_count,
  (SELECT count(*) FROM summaries) AS summaries_count,
  (SELECT count(*) FROM notes) AS notes_count,
  (SELECT count(*) FROM quizzes) AS quizzes_count,
  (SELECT count(*) FROM quiz_attempts) AS attempts_count,
  (SELECT count(*) FROM mastery_records) AS mastery_count,
  (SELECT count(*) FROM alembic_version) AS migrations_count;

-- ------------------------------------------------------------------------------
-- 2. USERS & MULTI-TENANT ISOLATION
-- ------------------------------------------------------------------------------

-- View recent user accounts (passwords are one-way bcrypt hashed)
SELECT id, email, name, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 5;

-- ------------------------------------------------------------------------------
-- 3. STUDY RESOURCES (PDFs & YOUTUBE VIDEOS)
-- ------------------------------------------------------------------------------

-- View latest ingested study materials
SELECT id, resource_id, source_type, title, status, created_at 
FROM resources 
ORDER BY created_at DESC 
LIMIT 5;

-- Find resources owned by a specific student (Multi-tenant check)
SELECT r.id, r.title, r.source_type, r.status, u.email
FROM resources r
JOIN users u ON r.user_id = u.id
ORDER BY r.created_at DESC
LIMIT 5;

-- ------------------------------------------------------------------------------
-- 4. CONVERSATIONS & CHAT HISTORY (RELATIONAL JOIN)
-- ------------------------------------------------------------------------------

-- View recent study conversation threads and their total message counts
SELECT 
    c.id AS conversation_id,
    c.title,
    c.scope_mode,
    c.created_at,
    count(m.id) AS total_messages
FROM conversations c
LEFT JOIN messages m ON c.id = m.conversation_id
GROUP BY c.id, c.title, c.scope_mode, c.created_at
ORDER BY c.created_at DESC
LIMIT 5;

-- View the actual back-and-forth dialogue for the most recent conversation
SELECT 
    m.role,
    m.content,
    m.sources_json,
    m.created_at
FROM messages m
WHERE m.conversation_id = (
    SELECT id FROM conversations ORDER BY updated_at DESC LIMIT 1
)
ORDER BY m.created_at ASC;

-- ------------------------------------------------------------------------------
-- 5. QUIZ ATTEMPTS & PERFORMANCE ANALYTICS
-- ------------------------------------------------------------------------------

-- View latest quiz submissions with scores and percentage
SELECT 
    qa.id,
    qa.topic,
    qa.score,
    qa.total_questions,
    qa.percentage,
    qa.attempted_at,
    u.email
FROM quiz_attempts qa
JOIN users u ON qa.user_id = u.id
ORDER BY qa.attempted_at DESC
LIMIT 5;

-- ------------------------------------------------------------------------------
-- 6. TOPIC MASTERY & SPACED REPETITION SCHEDULES
-- ------------------------------------------------------------------------------

-- View cumulative topic mastery scores and review schedules
SELECT 
    mr.topic,
    mr.mastery_score,
    mr.total_attempts,
    mr.total_questions,
    mr.correct_answers,
    mr.next_review_at,
    CASE 
        WHEN mr.next_review_at <= NOW() THEN 'Due for Review'
        WHEN mr.next_review_at IS NULL THEN 'Not Scheduled'
        ELSE 'Scheduled'
    END AS revision_status
FROM mastery_records mr
ORDER BY mr.next_review_at ASC NULLS LAST;

-- ------------------------------------------------------------------------------
-- 7. DATABASE INDEXES & PERFORMANCE (B-TREE INDEX PROOF)
-- ------------------------------------------------------------------------------

-- List all active indexes created by Alembic / SQLAlchemy
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Check active Alembic migration version
SELECT version_num FROM alembic_version;

-- ------------------------------------------------------------------------------
-- 8. REFERENTIAL INTEGRITY PROOFS (EXPLAIN IN VIVA)
-- ------------------------------------------------------------------------------

-- Foreign keys using ON DELETE CASCADE:
-- summaries, notes, quizzes, messages -> auto-delete when parent is deleted.

-- Foreign keys using ON DELETE SET NULL:
-- conversations.resource_id -> sets resource_id to NULL if resource is deleted,
-- preserving the student's conversation history!
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc 
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.referential_constraints AS rc
  ON tc.constraint_name = rc.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
  ON rc.unique_constraint_name = ccu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;
