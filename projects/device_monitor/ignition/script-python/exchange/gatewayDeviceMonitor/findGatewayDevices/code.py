"""
findGatewayDevices
v1.0.0 by The Baker Group

Purpose:
	Browse all devices configured under the Ignition OPC UA Server and create
	a folder structure under every writable tag provider that exposes the
	following device diagnostic values:

		Devices/
			Device_Name/
				Connected
				Hostname
				Name

	Any periods (.) in device names are replaced with underscores (_)
	because periods are not valid characters in Ignition tag names.

Usage:
	Save this script in a project library script named:

		exchange/gatewayDeviceMonitor/findGatewayDevices
	
	Execute using the built in Device Folder Setup View under the Exchange/Gateway Device Connection Monitor Folder
	
	You may also use a Gateway Event script to execute this script's primary functions buildDeviceDiagnosticTagsAllProviders() or buildDeviceDiagnosticTagsSpecific(provider)
	
To manually execute from the Script Console: 

		print exchange.gatewayDeviceMonitor.findGatewayDevices.buildDeviceDiagnosticTagsAllProviders()
		
	If targeting a specific provider or on the main gateway with multiple providers use
		
		print exchange.gatewayDeviceMonitor.findGatewayDevices.buildDeviceDiagnosticTagsSpecific(provider)
		
		input provider should be replaced with the name of the provider wanted i.e. [default] or default etc.

Notes:
	- The OPC item paths continue to use the ORIGINAL device name.
	- The created tag folder names use the SANITIZED device name.
	- Existing folders/tags are overwritten when rerun.
	- Only devices (such as modbus devices) with the Connected/Hostname/Name values will be created.
	- Only the OPC Ignition OPC UA Server is targeted, values can be changed below for other opc servers or folder names, update the views accordingly to match.
"""

# OPC UA server that contains the device diagnostics.
OPC_SERVER = "Ignition OPC UA Server"

# Root folder created in each tag provider.
OUTPUT_FOLDER = "Exchange/Gateway Device Connection Monitor/Devices"

# Tag group assigned to created OPC tags.
TAG_GROUP = "Default"

# Values the device must contain to be added to tag browser
REQUIRED_DIAGNOSTIC_VALUES = ["Connected", "Hostname", "Name"]

def getProviders():
	"""
	Returns a list of all tag providers except the System provider.

	"""
	providers = []

	for item in system.tag.browse(""):
		path = str(item["fullPath"])

		# Ignore the System provider.
		if path != "[System]":
			providers.append(path[1:-1])

	return providers


def getOpcDevices(opcServer=OPC_SERVER):
	"""
	Browse the OPC UA Server Devices folder and return all device names.

	"""
	devices = []

	for device in system.opc.browseServer(opcServer, "Devices"):
		deviceName = str(device.getDisplayName())

		# Remove surrounding brackets if present.
		if deviceName.startswith("[") and deviceName.endswith("]"):
			deviceName = deviceName[1:-1]

		devices.append(deviceName)

	return devices


def sanitizeTagName(name):
	"""
	Convert OPC device names into valid Ignition folder names.

	Example:
		EY1.RSB-A01.GATEWAY
			->
		EY1_RSB-A01_GATEWAY
	"""
	return str(name).replace(".", "_")


def createDeviceFolder(provider, deviceName, opcServer=OPC_SERVER):
	"""
	Create a folder for a device underneath:

		[provider]Exchange/Gateway Device Connection Monitor/Devices

	Then create three OPC tags:

		Connected
		Hostname
		Name

	Parameters:
		provider   - Tag provider name
		deviceName - Original OPC device name
		opcServer  - OPC UA server name
	"""

	# Folder name must be sanitized for Ignition.
	tagFolderName = sanitizeTagName(deviceName)

	deviceFolder = {
		"name": tagFolderName,
		"tagType": "Folder",
		"tags": [

			# Device Connected Status
			{
				"name": "Connected",
				"tagType": "AtomicTag",
				"valueSource": "opc",
				"opcServer": opcServer,
				"opcItemPath": "ns=1;s=[%s][Diagnostics]/Connected" % deviceName,
				"dataType": "Boolean",
				"tagGroup": TAG_GROUP
			},

			# Device Hostname
			{
				"name": "Hostname",
				"tagType": "AtomicTag",
				"valueSource": "opc",
				"opcServer": opcServer,
				"opcItemPath": "ns=1;s=[%s][Diagnostics]/Hostname" % deviceName,
				"dataType": "String",
				"tagGroup": TAG_GROUP
			},

			# Device Name
			{
				"name": "Name",
				"tagType": "AtomicTag",
				"valueSource": "opc",
				"opcServer": opcServer,
				"opcItemPath": "ns=1;s=[%s][Diagnostics]/Name" % deviceName,
				"dataType": "String",
				"tagGroup": TAG_GROUP
			}
		]
	}

	# Create or overwrite the device folder.
	return system.tag.configure(
		"[%s]%s" % (provider, OUTPUT_FOLDER),
		[deviceFolder],
		"o"
	)

def createDevicesFolder(provider):
	"""
	Ensure the root Devices folder exists in the provider.

	Example:
		[provider]Exchange/Gateway Device Connection Monitor/Devices
	"""

	outputPathParts = OUTPUT_FOLDER.split("/")
	baseFolderPath = "/".join(outputPathParts[:-1])
	rootFolderName = outputPathParts[-1]

	return system.tag.configure(
		"[%s]%s" % (provider, baseFolderPath),
		[{
			"name": rootFolderName,
			"tagType": "Folder"
		}],
		"m"
	)



def buildDeviceDiagnosticTagsAllProviders():
	"""
	Main execution function.

	Workflow:
		1. Find all tag providers.
		2. Find all OPC devices.
		3. Create Devices folder in each provider.
		4. Create a device folder for every OPC device.
		5. Create Connected, Hostname, and Name OPC tags.
		6. Return results for review.

	Returns:
		Dictionary containing creation results by provider.
	"""

	logger = system.util.getLogger("exchange.gatewayDeviceMonitor.DeviceDiagnosticTagBuilder")

	# Get all OPC devices.
	devices = getOpcDevices()

	# Get all tag providers.
	providers = getProviders()

	results = {}

	for provider in providers:
		results[provider] = []

		try:
			# Create root Devices folder.
			createDevicesFolder(provider)

			# Create device folders and tags.
			for deviceName in devices:
				if not deviceHasRequiredDiagnostics(deviceName):
					results[provider].append({
						"device": deviceName,
						"result": "Skipped: Missing one or more required diagnostics: %s"
							%', '.join(REQUIRED_DIAGNOSTIC_VALUES)
					})
					continue

				try:
					result = createDeviceFolder(
						provider,
						deviceName
					)

					results[provider].append({
						"device": deviceName,
						"result": result
					})

				except Exception as deviceError:

					logger.error(
						"Failed creating tags for provider %s, device %s: %s"
						% (provider, deviceName, deviceError)
					)

					results[provider].append({
						"device": deviceName,
						"result": "ERROR: %s" % deviceError
					})

		except Exception as providerError:

			logger.error(
				"Failed creating Devices folder for provider %s: %s"
				% (provider, providerError)
			)

			results[provider] = "ERROR: %s" % providerError

	return results


def normalizeProviderName(provider):
	"""
	Accepts:
		default
		[default]

	Returns:
		default
	"""
	provider = str(provider).strip()

	if provider.startswith("[") and provider.endswith("]"):
		provider = provider[1:-1]

	return provider


def buildDeviceDiagnosticTagsSpecific(provider):
	"""
	Create device diagnostic tags only in the specified tag provider.

	Example:
		print buildDeviceDiagnosticTags("default")
		print buildDeviceDiagnosticTags("[default]")
	"""

	logger = system.util.getLogger("exchange.gatewayDeviceMonitor.DeviceDiagnosticTagBuilder")

	provider = normalizeProviderName(provider)
	devices = getOpcDevices()

	results = {
		provider: []
	}

	try:
		createDevicesFolder(provider)
		
		for deviceName in devices:
			if not deviceHasRequiredDiagnostics(deviceName):
				results[provider].append({
					"device": deviceName,
					"result": "Skipped: Missing one or more required diagnostics: %s"
						% ", ".join(REQUIRED_DIAGNOSTIC_VALUES)
				})
				continue

			try:
				result = createDeviceFolder(provider, deviceName)

				results[provider].append({
					"device": deviceName,
					"result": result
				})

			except Exception as deviceError:
				logger.error(
					"Failed creating tags for provider %s, device %s: %s"
					% (provider, deviceName, deviceError)
				)

				results[provider].append({
					"device": deviceName,
					"result": "ERROR: %s" % deviceError
				})

	except Exception as providerError:
		logger.error(
			"Failed creating Devices folder for provider %s: %s"
			% (provider, providerError)
		)

		results[provider] = "ERROR: %s" % providerError

	return results


def getDeviceDiagnosticNames(deviceName, opcServer=OPC_SERVER):
	"""
	Return child names under:

		[deviceName][Diagnostics]
	"""
	names = []

	nodeId = "ns=1;s=[%s][Diagnostics]" % deviceName

	for item in system.opc.browseServer(opcServer, nodeId):
		names.append(str(item.getDisplayName()))

	return names


def deviceHasRequiredDiagnostics(deviceName, opcServer=OPC_SERVER):
	"""
	Only returns True if Connected, Hostname, and Name exist under Diagnostics.
	"""
	try:
		diagnosticNames = getDeviceDiagnosticNames(deviceName, opcServer)
		return all(name in diagnosticNames for name in REQUIRED_DIAGNOSTIC_VALUES)

	except Exception:
		return False	
	
   
def getProvidersWithDevices():
	"""
	Returns only providers that have at least one child item under:

		[provider]Exchange/Gateway Device Connection Monitor/Devices

	Intended to be used after running:

		buildDeviceDiagnosticTagsAllProviders()

	"""

	logger = system.util.getLogger("exchange.gatewayDeviceMonitor.DeviceDiagnosticTagBuilder")
	providersWithDevices = []

	for provider in getProviders():
		devicesPath = "[%s]%s" % (provider, OUTPUT_FOLDER)

		try:
			browseResults = system.tag.browse(devicesPath)

			for item in browseResults:
				# A valid device entry should be a folder under Devices.
				if str(item["tagType"]) == "Folder":
					providersWithDevices.append(provider)
					break

		except Exception as e:
			logger.warn(
				"Skipping provider %s. Could not browse %s: %s"
				% (provider, devicesPath, e)
			)

	return providersWithDevices
	