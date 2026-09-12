-- PostgreSQL only. Apply once to an existing normalized SkillSwap database.
-- Take a backup and run during the release before starting the new application.
BEGIN;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema=current_schema() AND table_name='messages' AND column_name='read_at') THEN
        ALTER TABLE messages ADD COLUMN read_at TIMESTAMP WITHOUT TIME ZONE;
        UPDATE messages SET read_at = CURRENT_TIMESTAMP AT TIME ZONE 'UTC';
    END IF;
END $$;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS client_id VARCHAR(36);
CREATE UNIQUE INDEX IF NOT EXISTS uq_message_sender_client ON messages (sender_id, client_id);
CREATE INDEX IF NOT EXISTS ix_message_unread ON messages (conversation_id, receiver_id, read_at);
-- The original model defined the partial predicate only for SQLite.
DROP INDEX IF EXISTS ix_swap_pending_pair;
CREATE UNIQUE INDEX ix_swap_pending_pair ON swap_requests (requester_id, requested_skill_id) WHERE status = 'pending';
COMMIT;
