-- "Did it actually work?" SQL questions on BatchGuard's database (SQLite; standard SQL).
-- Run: sqlite3 batchguard.sqlite3 < qa/product_questions.sql

-- 1. How many batches are in each status?
SELECT status, COUNT(*) AS batches FROM batches GROUP BY status ORDER BY batches DESC;

-- 2. Right-first-time rate: share of released batches with no deviation.
SELECT ROUND(100.0 * SUM(CASE WHEN d.batch_id IS NULL THEN 1 ELSE 0 END) / COUNT(*), 1) AS right_first_time_pct
FROM batches b
LEFT JOIN (SELECT DISTINCT batch_id FROM deviations) d ON d.batch_id = b.id
WHERE b.status = 'released';

-- 3. Which steps go out of spec most often? (where to focus process improvement)
SELECT ts.seq, ts.parameter, COUNT(*) AS deviations
FROM deviations dv
JOIN step_entries se ON se.id = dv.step_entry_id
JOIN template_steps ts ON ts.id = se.step_id
GROUP BY ts.seq, ts.parameter ORDER BY deviations DESC;

-- 4. Correction rate by user (training signal, not blame).
SELECT u.username, COUNT(*) AS entries, SUM(CASE WHEN se.correction_reason IS NOT NULL THEN 1 ELSE 0 END) AS corrections
FROM step_entries se JOIN users u ON u.id = se.recorded_by
GROUP BY u.username ORDER BY corrections DESC;

-- 5. Review cycle time: submit-for-review to release, in hours.
SELECT b.batch_no,
       ROUND((julianday(rel.signed_at) - julianday(rev.signed_at)) * 24, 2) AS hours_in_review
FROM batches b
JOIN signatures rev ON rev.record_type = 'batch' AND rev.record_id = b.id AND rev.meaning = 'reviewed'
JOIN signatures rel ON rel.record_type = 'batch' AND rel.record_id = b.id AND rel.meaning = 'approved_release'
ORDER BY hours_in_review DESC;

-- 6. Failed signature attempts in the last 7 days (security review).
SELECT username, COUNT(*) AS failed_signatures
FROM audit_trail WHERE action = 'signature_failed' AND at >= datetime('now', '-7 days')
GROUP BY username ORDER BY failed_signatures DESC;
