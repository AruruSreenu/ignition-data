def handleTimerEvent():
	import AlarmUtils
	
	try:
	    alarmDataset, activeAlarmCount = AlarmUtils.getTop3ActiveAlarms()
	
	    tagPaths = [
	        "[AIRCO]AlarmUtils/Top3ActiveAlarms",
	        "[AIRCO]AlarmUtils/ActiveAlarmCount"
	    ]
	
	    values = [
	        alarmDataset,
	        activeAlarmCount
	    ]
	
	    results = system.tag.writeBlocking(tagPaths, values)
	
	except Exception as e:
	    print "Alarm Timer Error:", str(e)