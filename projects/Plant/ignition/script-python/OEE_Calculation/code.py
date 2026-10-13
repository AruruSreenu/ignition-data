from datetime import datetime
from time import time
import system

def oeeCalculation():
   logger = system.util.getLogger("OEE_Gateway")
  
   def safe_div(numerator, denominator):
       try:
           if denominator in (None, 0):
               return 0.0
           return float(numerator) / float(denominator)
       except Exception:
           return 0.0
  
   def compute_oee(planned_prod_seconds, run_seconds, total_count, good_count, ideal_cycle_seconds):
       # Availability
       availability = safe_div(run_seconds, planned_prod_seconds)
  
       # Performance
       # Expected production time = ideal_cycle_seconds * total_count
       # Performance = expected_production_time / run_seconds
       performance = 0.0
       if run_seconds > 0:
           expected_time = float(ideal_cycle_seconds) * float(total_count)
           performance = safe_div(expected_time, run_seconds)
       else:
           performance = 0.0
  
       # Quality
       quality = safe_div(good_count, total_count)
  
       # OEE
       oee = availability * performance * quality
  
       # Clip between 0 and 1
       availability = max(0.0, min(availability, 1.0))
       performance  = max(0.0, min(performance,  2.0))  # performance could be >1 if faster than ideal; cap if desired
       quality = max(0.0, min(quality, 1.0))
       oee = max(0.0, min(oee, 1.0))
  
       return {
           "availability": availability,
           "performance": performance,
           "quality": quality,
           "oee": oee
       }
  
   # Read tags in one call
   tag_paths = [
       "[default]OEE Calculator/PlannedProductionSeconds",
       "[default]OEE Calculator/RunSeconds",
       "[default]OEE Calculator/TotalCount",
       "[default]OEE Calculator/GoodCount",
       "[default]OEE Calculator/IdealCycleTime"
   ]
  
   try:
       results = system.tag.readBlocking(tag_paths)
       # parse values with defaults
       planned_prod_seconds = results[0].value if results[0].value is not None else 0
       run_seconds = results[1].value if results[1].value is not None else 0
       total_count = results[2].value if results[2].value is not None else 0
       good_count = results[3].value if results[3].value is not None else 0
       ideal_cycle_seconds = results[4].value if results[4].value is not None else 1.0
  
       metrics = compute_oee(planned_prod_seconds, run_seconds, total_count, good_count, ideal_cycle_seconds)
  
       # Convert to percentages for tag writes (0-100)
       avail_pct = round(metrics["availability"] * 100.0, 2)
       perf_pct  = round(metrics["performance"] * 100.0, 2)
       qual_pct  = round(metrics["quality"] * 100.0, 2)
       oee_pct   = round(metrics["oee"] * 100.0, 2)
  
       # Write back to tags (so clients/SCADA can display)
       write_paths = [
           "[default]OEE Calculator/OEE_AvailabilityPct",
           "[default]OEE Calculator/OEE_PerformancePct",
           "[default]OEE Calculator/OEE_QualityPct",
           "[default]OEE Calculator/OEE_OverallPct"
       ]
       write_values = [avail_pct, perf_pct, qual_pct, oee_pct]
       system.tag.writeBlocking(write_paths, write_values)
  
       logger.info("OEE computed: Availability={}%, Performance={}%, Quality={}%, OEE={}%"\
                   .format(avail_pct, perf_pct, qual_pct, oee_pct))
  
       # OPTIONAL: log into a database table for history
       # Prepare SQL (use parameterized query)
       # Table: OEE_Log(machine_id, ts_utc, planned_seconds, run_seconds, total_count, good_count, ideal_cycle_seconds, availability, performance, quality, oee)
       insert_sql = """
           INSERT INTO OEE_Log
           (machine_id, ts_utc, planned_seconds, run_seconds, total_count, good_count, ideal_cycle_seconds,
            availability_pct, performance_pct, quality_pct, oee_pct)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
       """
       machine_id = "PHARMA_LINE_01"
       ts_now = system.date.now()  # gateway server timestamp
       params = [machine_id, ts_now, planned_prod_seconds, run_seconds, total_count, good_count, ideal_cycle_seconds,
                 avail_pct, perf_pct, qual_pct, oee_pct]
  
       # Choose your DB connection name in the Designer (e.g. 'LocalDB')
       try:
           system.db.runPrepUpdate(insert_sql, params, "LIMS")
           system.vision.showMessage("OEE Logs Data Added Successfully", "OEE LOGS")
       except Exception, e:
           logger.warn("Failed to log OEE to DB: %s" % str(e))
  
   except Exception, e:
       logger.error("Error computing OEE: %s" % str(e))