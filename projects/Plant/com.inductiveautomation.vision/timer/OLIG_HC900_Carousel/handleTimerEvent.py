def handleTimerEvent():
	plantWindows = [
		"PID/OLIG_HC900_1",
		"PID/OLIG_HC900_2",
		"PID/CTP_3",
		"PID/CTP_4",
		"PID/CTP_5",
		"PID/CTP_6",
		"PID/CTP_7",
		"PID/CTP_8",
		"PID/CTP_9",
		"PID/CTP_10"
	]
	
	activeTag = "[client]TopMenu/ActiveTopMenu"
	plantIndexTag = "[client]TopMenu/PlantViewIndex"
	animationTag = "[client]TopMenu/ChangeAnimation"
	
	tagValues = system.tag.readBlocking([
		activeTag,
		plantIndexTag,
		animationTag
	])
	
	activeButton = tagValues[0].value
	currentIndex = tagValues[1].value
	changeAnimation = tagValues[2].value
	
	# Run animation only when:
	# 1. ChangeAnimation is True
	# 2. Plant View is the active top menu
	if bool(changeAnimation) and activeButton == "Plant View":
	
		try:
			currentIndex = int(currentIndex)
		except:
			currentIndex = 0
	
		# Prevent invalid index values
		if currentIndex < 0 or currentIndex >= len(plantWindows):
			currentIndex = 0
	
		# Calculate next window index
		nextIndex = (currentIndex + 1) % len(plantWindows)
	
		# Navigate to next Plant View window
		system.nav.swapTo(plantWindows[nextIndex])
	
		# Save current index
		system.tag.writeBlocking(
			[plantIndexTag],
			[nextIndex]
		)