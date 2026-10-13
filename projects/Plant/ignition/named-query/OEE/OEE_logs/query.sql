SELECT
    id,
    machine_id,
    ts_utc,
    planned_seconds,
    run_seconds,
    total_count,
    good_count,
    ideal_cycle_seconds,
    availability_pct,
    performance_pct,
    quality_pct,
    oee_pct,
    created_at
FROM OEE_Log
WHERE machine_id = :machineId
ORDER BY ts_utc DESC;