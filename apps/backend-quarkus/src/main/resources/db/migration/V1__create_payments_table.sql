CREATE TABLE IF NOT EXISTS payments (
    id          VARCHAR(36)     PRIMARY KEY,
    amount      NUMERIC(10, 2)  NOT NULL,
    card_number VARCHAR(19)     NOT NULL,
    status      VARCHAR(20)     NOT NULL,
    external_id VARCHAR(50),
    created_at  TIMESTAMP       NOT NULL
);
