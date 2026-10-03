CREATE OR REPLACE VIEW mrt_campaign_stats AS
SELECT 
    COUNT(*) AS total_campaigns,
    COUNT(CASE WHEN total_raised >= goal THEN 1 END) AS successful_campaigns,
    COUNT(CASE WHEN total_raised < goal AND deadline < NOW() THEN 1 END) AS failed_campaigns,
    COUNT(CASE WHEN total_raised < goal AND deadline >= NOW() THEN 1 END) AS active_campaigns,
    COALESCE(SUM(total_raised), 0) AS total_raised_sum,
    COALESCE(AVG(total_raised), 0) AS avg_raised_per_campaign
FROM campaigns;

CREATE OR REPLACE VIEW mrt_top_sponsors AS
SELECT 
    (event_data->>'contributor')::VARCHAR AS sponsor_address,
    SUM((event_data->>'amount')::NUMERIC) AS total_contributed
FROM raw_events
WHERE event_name = 'Contributed'
GROUP BY sponsor_address
ORDER BY total_contributed DESC
LIMIT 5;