SELECT plant_pid_name 
FROM plant_selection
WHERE (:PlantName = 'ALL' or plant_pid_name = :PlantName)