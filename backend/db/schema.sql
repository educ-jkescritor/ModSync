CREATE TABLE IF NOT EXISTS uploads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  filename TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  pages_analyzed INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detections (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  upload_id INTEGER NOT NULL,
  technology TEXT NOT NULL,
  alias TEXT NOT NULL,
  page INTEGER NOT NULL,
  start_offset INTEGER NOT NULL,
  end_offset INTEGER NOT NULL,
  category TEXT NOT NULL,
  lifecycle_risk INTEGER NOT NULL,
  FOREIGN KEY (upload_id) REFERENCES uploads(id)
);

CREATE TABLE IF NOT EXISTS recommendations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  upload_id INTEGER NOT NULL,
  technology TEXT NOT NULL,
  review_priority TEXT NOT NULL,
  priority_score INTEGER NOT NULL,
  confidence_score REAL NOT NULL,
  pages_json TEXT NOT NULL,
  recommendation_json TEXT NOT NULL,
  faculty_validation_required INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (upload_id) REFERENCES uploads(id)
);

CREATE INDEX IF NOT EXISTS idx_detections_upload_id ON detections(upload_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_upload_id ON recommendations(upload_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_priority ON recommendations(review_priority);

