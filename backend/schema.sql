CREATE TABLE IF NOT EXISTS raw_events (
    id SERIAL PRIMARY KEY,
    transaction_hash VARCHAR(66) NOT NULL,
    block_number BIGINT NOT NULL,
    block_timestamp TIMESTAMP NOT NULL,
    event_name VARCHAR(50) NOT NULL,
    campaign_id INT NOT NULL,
    event_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_raw_events_event_name ON raw_events(event_name);
CREATE INDEX IF NOT EXISTS idx_raw_events_campaign_id ON raw_events(campaign_id);

CREATE TABLE IF NOT EXISTS campaigns (
    campaign_id INT PRIMARY KEY,
    creator VARCHAR(42) NOT NULL,
    goal NUMERIC NOT NULL,
    deadline TIMESTAMP NOT NULL,
    total_raised NUMERIC DEFAULT 0,
    claimed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);