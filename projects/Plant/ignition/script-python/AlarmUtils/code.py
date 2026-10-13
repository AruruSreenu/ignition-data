def getTop3ActiveAlarms():
	# remove the ClearUnacked in state list
    alarms = system.alarm.queryStatus(
        state=["ActiveUnacked", "ActiveAcked", "ClearUnacked"]
    )

    rows = []

    for alarm in alarms:

        eventTime = alarm["EventTime"]
        displayPath = str(alarm["DisplayPath"])
        priority = str(alarm["Priority"])
        state = str(alarm["State"])

        rows.append([
            eventTime,
            displayPath,
            priority,
            state
        ])

    # Sort newest first
    rows.sort(
        key=lambda x: x[0],
        reverse=True
    )

    # Total active alarm count
    activeAlarmCount = len(rows)

    # Latest 3 alarms
    top3 = rows[:3]

    headers = [
        "EventTime",
        "DisplayPath",
        "Priority",
        "State"
    ]

    alarmDataset = system.dataset.toDataSet(
        headers,
        top3
    )

    return alarmDataset, activeAlarmCount