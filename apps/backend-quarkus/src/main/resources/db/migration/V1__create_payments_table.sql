-- TCC Performance Comparison — Schema inicial
-- Java 25 Virtual Threads vs Go 1.25 Goroutines
-- Simetrico ao schema criado via SQL no backend Go (main.go)

CREATE TABLE IF NOT EXISTS payments (
    id VARCHAR(36) PRIMARY KEY,
    amount NUMERIC(10, 2) NOT NULL,
    card_number VARCHAR(19) NOT NULL,
    status VARCHAR(20) NOT NULL,
    external_id VARCHAR(50),
    created_at TIMESTAMP NOT NULL
);
