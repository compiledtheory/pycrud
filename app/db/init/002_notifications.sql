CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    content TEXT NOT NULL,
    channel VARCHAR(32) NOT NULL,
    recipient VARCHAR(255) NOT NULL,
    scheduled_at TIMESTAMPTZ NOT NULL,
    timezone VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    idempotency_key VARCHAR UNIQUE NOT NULL
);

ALTER TABLE notifications
    ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR;

UPDATE notifications
SET idempotency_key = 'notif_' || gen_random_uuid()::text
WHERE idempotency_key IS NULL;

ALTER TABLE notifications
    ALTER COLUMN idempotency_key SET NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS notifications_idempotency_key_key
    ON notifications (idempotency_key);
