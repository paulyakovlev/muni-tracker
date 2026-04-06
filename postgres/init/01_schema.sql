CREATE TABLE IF NOT EXISTS stop_predictions (
    id SERIAL PRIMARY KEY,
    recorded_at TIMESTAMPTZ,
    stop_code TEXT,
    line TEXT,
    direction TEXT,
    vehicle_id TEXT,
    aimed_arrival TIMESTAMPTZ,
    expected_arrival TIMESTAMPTZ,
    occupancy TEXT,
    fetched_at TIMESTAMPTZ
);

CREATE UNIQUE INDEX IF NOT EXISTS uniq_prediction
    ON stop_predictions (stop_code, vehicle_id, expected_arrival);

CREATE TABLE IF NOT EXISTS vehicle_positions (
    vehicle_id TEXT PRIMARY KEY,
    line TEXT,
    direction TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    fetched_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS stops (
    stop_id TEXT PRIMARY KEY,
    stop_name TEXT,
    direction TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);
