-- Monitoring tables for model performance metrics and alerts

-- Table for model information
CREATE TABLE IF NOT EXISTS model_metadata (
    model_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    model_type TEXT,
    target_variable TEXT,
    owner TEXT
);

-- Table for model metrics
CREATE TABLE IF NOT EXISTS model_metrics (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (model_id) REFERENCES model_metadata(model_id)
);

-- Table for alert rules
CREATE TABLE IF NOT EXISTS alert_rules (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    rule_name TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    threshold REAL NOT NULL,
    operator TEXT NOT NULL,
    severity TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    description TEXT,
    FOREIGN KEY (model_id) REFERENCES model_metadata(model_id)
);

-- Table for triggered alerts
CREATE TABLE IF NOT EXISTS alert_events (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    model_id TEXT NOT NULL,
    model_version TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    threshold REAL NOT NULL,
    actual_value REAL NOT NULL,
    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    severity TEXT NOT NULL,
    acknowledged BOOLEAN DEFAULT 0,
    acknowledged_at TIMESTAMP,
    acknowledged_by TEXT,
    resolution_notes TEXT,
    FOREIGN KEY (rule_id) REFERENCES alert_rules(id),
    FOREIGN KEY (model_id) REFERENCES model_metadata(model_id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_model_metrics_model_id ON model_metrics(model_id);
CREATE INDEX IF NOT EXISTS idx_model_metrics_model_version ON model_metrics(model_version);
CREATE INDEX IF NOT EXISTS idx_model_metrics_metric_name ON model_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_model_metrics_timestamp ON model_metrics(timestamp);

CREATE INDEX IF NOT EXISTS idx_alert_rules_model_id ON alert_rules(model_id);
CREATE INDEX IF NOT EXISTS idx_alert_rules_model_version ON alert_rules(model_version);
CREATE INDEX IF NOT EXISTS idx_alert_rules_metric_name ON alert_rules(metric_name);

CREATE INDEX IF NOT EXISTS idx_alert_events_model_id ON alert_events(model_id);
CREATE INDEX IF NOT EXISTS idx_alert_events_model_version ON alert_events(model_version);
CREATE INDEX IF NOT EXISTS idx_alert_events_rule_id ON alert_events(rule_id);
CREATE INDEX IF NOT EXISTS idx_alert_events_triggered_at ON alert_events(triggered_at);
