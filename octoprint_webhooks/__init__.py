# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import requests
import time

from io import BytesIO
from PIL import Image

import octoprint.plugin
from octoprint.events import eventManager, Events


# Replaces any v in data that start with @param
# with the v in values. For instance, if data
# was {"abc":"@p1"}, and values was {"p1":"123"},
# then @p1 would get replaced with 123 like so:
# {"abc":"123"}
def replace_dict_with_data(d, v):
	looping_over = d
	if type(d) is list:
		looping_over = range(0, len(d))
	for key in looping_over:
		value = d[key]
		if type(value) is dict:
			d[key] = replace_dict_with_data(value, v)
		elif type(value) is str:
			# Loop until all @params are replaced
			while type(d[key]) is str and d[key].find("@") >= 0:
				start_index = d[key].find("@")
				# Find the end text by space
				end_index = d[key].find(" ", start_index)
				if end_index == -1:
					end_index = len(d[key])
				value_key = d[key][start_index + 1:end_index]
				# Check for dot notation
				components = value_key.split(".")
				current_v = v
				comp_found = True
				for ic in range(0, len(components)):
					comp = components[ic]
					if comp in current_v:
						current_v = current_v[comp]
					else:
						comp_found = False
						break
				if not comp_found:
					current_v = ""
				if start_index == 0 and end_index == len(d[key]):
					d[key] = current_v
				else:
					d[key] = d[key].replace(d[key][start_index:end_index], str(current_v))
		elif type(value) is list:
			d[key] = replace_dict_with_data(value, v)
	return d

# Checks for the name/value pair to make sure it matches
# and if not sets the name/value and returns
def check_for_header(headers, name, value):
	is_set = False
	for key in headers:
		if name.lower() in key.lower():
			is_set = True
			if value.lower() not in headers[key].lower():
				headers[key] = value
	if not is_set:
		headers[name] = value
	return headers


class WebhooksPlugin(octoprint.plugin.StartupPlugin, octoprint.plugin.TemplatePlugin, octoprint.plugin.SettingsPlugin,
					 octoprint.plugin.EventHandlerPlugin, octoprint.plugin.AssetPlugin, octoprint.plugin.SimpleApiPlugin,
					 octoprint.plugin.ProgressPlugin):
	def __init__(self):
		self.triggered = False
		self.last_print_progress = -1
		self.last_print_progress_milestone = 0

	def get_update_information(self, *args, **kwargs):
		return dict(
			webhooks=dict(
				displayName=self._plugin_name,
				displayVersion=self._plugin_version,
				type="github_release",
				current=self._plugin_version,
				user="2blane",
				repo="OctoPrint-Webhooks",
				pip="https://github.com/2blane/OctoPrint-Webhooks/archive/{target}.zip"
			)
		)

	def on_after_startup(self):
		self._logger.info("Hello World from WebhooksPlugin! " + self._settings.get(["url"]))

	def get_settings_defaults(self):
		return dict(url="", apiSecret="", deviceIdentifier="",
					eventPrintStarted=True, eventPrintDone=True, eventPrintFailed=True, eventPrintPaused=True,
					eventUserActionNeeded=True, eventError=True,
					event_print_progress=False, event_print_progress_interval="50",
					headers='{\n  "Content-Type": "application/json"\n}',
					data='{\n  "deviceIdentifier":"@deviceIdentifier",\n  "apiSecret":"@apiSecret",\n  "topic":"@topic",\n  "message":"@message",\n  "extra":"@extra"\n}',
					http_method="POST",
					content_type="JSON",
					oauth=False,
					oauth_url="",
					oauth_headers='{\n  "Content-Type": "application/json"\n}',
					oauth_data='{\n  "client_id":"myClient",\n  "client_secret":"mySecret",\n  "grant_type":"client_credentials"\n}',
					oauth_http_method="POST",
					oauth_content_type="JSON",
					test_event="PrintStarted"
					)

	def get_template_configs(self):
		return [
			dict(type="settings", custom_bindings=True)
		]

	def get_assets(self):
		return dict(
			css=["css/webhooks.css"],
			js=["js/webhooks.js"]
		)

	def register_custom_events(self, *args, **kwargs):
		return ["notify", "progress"]

	def on_print_progress(self, storage, path, progress):
		# Reset in case of multiple prints
		if self.last_print_progress > progress:
			self.last_print_progress = -1
		# Get the settings
		active = self._settings.get(["event_print_progress"])
		event_print_progress_interval = self._settings.get(["event_print_progress_interval"])
		#self._logger.info("Print Progress" + storage + " - " + path + " - {0}".format(progress))
		if active:
			try:
				interval = int(event_print_progress_interval)
				# Now loop over all the missed progress events and see if they match
				for p in range(self.last_print_progress + 1, progress + 1):
					if p % interval == 0 and p != 0 and p != 100:
						# Send the event for print progress
						self.last_print_progress_milestone = p
						eventManager().fire(Events.PLUGIN_WEBHOOKS_PROGRESS)
				# Update the last print progress
				self.last_print_progress = progress
			except Exception as e:
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", hide=True, msg="Invalid Setting for PRINT PROGRESS INTERVAL please use a number without any special characters instead of " + event_print_progress_interval))
				return

	def get_api_commands(self):
		return dict(
			testhook=[]
		)

	def on_api_command(self, command, data):
		if command == "testhook":
			# self._logger.info("API testhook CALLED!")
			# TRIGGER A CUSTOM EVENT FOR A TEST PAYLOAD
			event_name = ""
			if "event" in data:
				event_name = data["event"]
			if event_name == "plugin_webhooks_progress":
				self.last_print_progress_milestone = 50
			self.on_event(event_name, {
				"name": "example.gcode",
				"path": "example.gcode",
				"origin": "local",
				"size": 242038,
				"owner": "example_user",
				"time": 50.237335886,
				"popup": True
			})

	# Returns a dictionary of the current job information
	def get_job_information(self):
		# Call the api
		try:
			rd = self._printer.get_current_data()
			# Get the path if it exists
			if "job" in rd and "file" in rd["job"] and "path" in rd["job"]["file"]:
				path = rd["job"]["file"]["path"]
				if type(path) is str:
					if self._file_manager.file_exists(rd["job"]["file"]["origin"], path):
						# self._logger.info("file exists at path")
						# Get the file metadata, analysis, ...
						meta = self._file_manager.get_metadata(rd["job"]["file"]["origin"], path)
						metadata = {
							"meta": meta
						}
						rd.update(metadata)
					else:
						self._logger.info("file does not exist at path")
			# self._logger.info("getting job info" + json.dumps(rd))
			return rd
		except Exception as e:
			self._logger.info("get_job_information exception: " + str(e))
			return {}

	def on_event(self, event, payload):
		topic = "Unknown"
		message = "Unknown"
		extra = payload
		# 0) Determine the topic and message parameters and if we are parsing this event.
		if event == Events.PRINT_STARTED and self._settings.get(["eventPrintStarted"]):
			topic = "Print Started"
			message = "Your print has started."
		elif event == Events.PRINT_DONE and self._settings.get(["eventPrintDone"]):
			topic = "Print Done"
			message = "Your print is done."
		elif event == Events.PRINT_FAILED and self._settings.get(["eventPrintFailed"]):
			topic = "Print Failed"
			message = "Something went wrong and your print has failed."
		elif event == Events.PRINT_PAUSED and self._settings.get(["eventPrintPaused"]):
			topic = "Print Paused"
			message = "Your print has paused. You might need to change the filament color."
		elif event == Events.PLUGIN_WEBHOOKS_NOTIFY and self._settings.get(["eventUserActionNeeded"]):
			topic = "User Action Needed"
			message = "User action is needed. You might need to change the filament color."
		elif event == Events.PLUGIN_WEBHOOKS_PROGRESS and self._settings.get(["event_print_progress"]):
			topic = "Print Progress"
			message = "Your print is {0}% complete".format(self.last_print_progress_milestone)
		elif event == Events.ERROR and self._settings.get(["eventError"]):
			topic = "Error"
			message = "There was an error."
		else:
			return
		self._logger.info("P EVENT " + topic + " - " + message)
		# 1) If necessary, make an OAuth request to get back an access token.
		oauth = self._settings.get(["oauth"])
		oauth_result = dict()
		oauth_passed = False
		if oauth:
			parsed_oauth_headers = False
			try:
				# 1.1) Get the request data and headers
				oauth_url = self._settings.get(["oauth_url"])
				oauth_headers = json.loads(self._settings.get(["oauth_headers"]))
				parsed_oauth_headers = True
				oauth_data = json.loads(self._settings.get(["oauth_data"]))
				oauth_http_method = self._settings.get(["oauth_http_method"])
				oauth_content_type = self._settings.get(["oauth_content_type"])
				# 1.2) Send the request
				self._logger.info("Sending OAuth Request")
				response = ""
				if oauth_http_method == "GET":
					response = requests.get(oauth_url, params=oauth_data, headers=oauth_headers)
				else:
					if oauth_content_type == "JSON":
						# Make sure the Content-Type header is set to application/json
						oauth_headers = check_for_header(oauth_headers, "content-type", "application/json")
						# self._logger.info("oauth headers: " + json.dumps(oauth_headers) + " - data: " + json.dumps(oauth_data))
						# self._logger.info("oauth_http_method: " + oauth_http_method + " - oauth_content_type: " + oauth_content_type)
						response = requests.request(oauth_http_method, oauth_url, json=oauth_data, headers=oauth_headers)
					else:
						# Make sure the Content-Type header is set to application/x-www-form-urlencoded
						oauth_headers = check_for_header(oauth_headers, "content-type", "application/x-www-form-urlencoded")
						# self._logger.info("oauth headers: " + json.dumps(oauth_headers) + " - data: " + json.dumps(oauth_data))
						# self._logger.info("oauth_http_method: " + oauth_http_method + " - oauth_content_type: " + oauth_content_type)
						response = requests.request(oauth_http_method, oauth_url, data=oauth_data, headers=oauth_headers)
				# 1.3) Check to make sure we got a valid response code.
				self._logger.info("OAuth Response: " + " - " + response.text)
				code = response.status_code
				if 200 <= code < 400:
					oauth_result = response.json()
					oauth_passed = True
					self._logger.info("OAuth Passed")
				else:
					self._logger.info("Invalid OAuth Response Code %s" % code)
					self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", hide=False, msg="Invalid OAuth Response: " + response.text))
			except requests.exceptions.RequestException as e:
				self._logger.info("OAuth API Error: " + str(e))
			except Exception as e:
				if parsed_oauth_headers:
					self._logger.info("OAuth JSON Parse Issue for DATA")
					self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", msg="Invalid JSON for Webhooks OAUTH DATA Settings"))
				else:
					self._logger.info("OAuth JSON Parse Issue for HEADERS")
					self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", msg="Invalid JSON for Webhooks OAUTH HEADERS Settings"))
		else:
			oauth_passed = True
		# Make sure we passed the oauth check
		if not oauth_passed:
			# Oauth not passed
			self._logger.info("Not sending request - OAuth not passed")
			return
		# Send the notification
		# 2) Call the API
		parsed_headers = 0
		try:
			url = self._settings.get(["url"])
			api_secret = self._settings.get(["apiSecret"])
			device_identifier = self._settings.get(["deviceIdentifier"])
			headers = json.loads(self._settings.get(["headers"]))
			parsed_headers = 1
			data = json.loads(self._settings.get(["data"]))
			parsed_headers = 2
			http_method = self._settings.get(["http_method"])
			content_type = self._settings.get(["content_type"])
			# 2.1) Create a dictionary of all possible replacement variables.
			values = {}
			if extra is dict:
				values = extra
			values2 = {
				"topic": topic,
				"message": message,
				"apiSecret": api_secret,
				"deviceIdentifier": device_identifier,
				"extra": extra,
				"currentTime": int(time.time())
			}
			values.update(values2)
			# 2.2) Get the current job information from the API
			job_info = self.get_job_information()
			job_values = {}
			job_keys = ["state", "job", "currentZ", "progress", "offsets", "meta"]
			for jit in range(0, len(job_keys)):
				if job_keys[jit] in job_info:
					job_values[job_keys[jit]] = job_info[job_keys[jit]]
			values.update(job_values)
			# 2.3) Get a snapshot image if necessary
			uploading_file = False
			uploading_file_name = ""
			for uk in data:
				if data[uk] == "@snapshot":
					uploading_file = True
					uploading_file_name = uk
					break
			snap = None
			if uploading_file:
				del data[uploading_file_name]
				snap = self.get_snapshot()
				if snap is not None:
					self._logger.info("snapshot retrieved")
				else:
					uploading_file = False
			# 2.4) Merge these values with the oauth values.
			values.update(oauth_result)
			# 2.5) Replace the data and header elements that start with @
			data = replace_dict_with_data(data, values)
			headers = replace_dict_with_data(headers, values)
			# 2.6) Send the request
			response = ""
			if http_method == "GET":
				# Note: we can't upload a file with GET.
				response = requests.get(url, params=data, headers=headers)
			else:
				if uploading_file:
					# Delete the Content-Type header if provided so that requests can set it on its own
					to_remove = []
					for hk in headers:
						if "content-type" in hk.lower():
							to_remove.append(hk)
					for el in to_remove:
						del headers[el]
					self._logger.info("headers: " + json.dumps(headers))
					self._logger.info("data: " + json.dumps(data))
					self._logger.info("http_method: " + http_method + " - content_type: " + content_type)
					self._logger.info("sending snapshot as parameter: " + uploading_file_name)
					files = {
						uploading_file_name: ("snapshot.jpg", snap, "image/jpeg")
					}
					response = requests.request(http_method, url, files=files, data=data, headers=headers)
				elif content_type == "JSON":
					# Make sure the Content-Type header is set to application/json
					headers = check_for_header(headers, "content-type", "application/json")
					self._logger.info("headers: " + json.dumps(headers))
					self._logger.info("data: " + json.dumps(data))
					self._logger.info("http_method: " + http_method + " - content_type: " + content_type)
					response = requests.request(http_method, url, json=data, headers=headers)
				else:
					# Make sure the Content-Type header is set to application/x-www-form-urlencoded
					headers = check_for_header(headers, "content-type", "application/x-www-form-urlencoded")
					self._logger.info("headers: " + json.dumps(headers))
					self._logger.info("data: " + json.dumps(data))
					self._logger.info("http_method: " + http_method + " - content_type: " + content_type)
					response = requests.request(http_method, url, data=data, headers=headers)
			self._logger.info("Response: " + response.text)
			# Try to parse the response if possible.
			code = response.status_code
			if 200 <= code < 400:
				self._logger.info("API SUCCESS: " + event + " " + response.text)
				# Optionally show a message of success if the payload has popup=True
				if type(payload) is dict and "popup" in payload:
					self._plugin_manager.send_plugin_message(self._identifier, dict(type="success", hide=True, msg="Response: " + response.text))
			else:
				self._logger.info("API Bad Response Code: %s" % code)
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", hide=False, msg="Invalid API Response: " + response.text))
		except requests.exceptions.RequestException as e:
			self._logger.info("API ERROR: " + str(e))
		except Exception as e:
			if parsed_headers == 1:
				self._logger.info("JSON Parse DATA Issue: " + str(e))
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", msg="Invalid JSON for Webhooks DATA Setting"))
			elif parsed_headers == 0:
				self._logger.info("JSON Parse HEADERS Issue: " + str(e))
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", msg="Invalid JSON for Webhooks HEADERS Setting"))
			else:
				self._logger.info("Unknown Issue: " + str(e))
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", msg="Unknown Issue when trying to call API."))

	def recv_callback(self, comm_instance, line, *args, **kwargs):
		# Found keyword, fire event and block until other text is received
		if "echo:busy: paused for user" in line:
			if not self.triggered:
				eventManager().fire(Events.PLUGIN_WEBHOOKS_NOTIFY)
				self.triggered = True
		# Other text, we may fire another event if we encounter "paused for user" again
		else:
			self.triggered = False
		return line

		# Private functions - Print Job Notifications

	# Create an image by getting an image from the setting webcam-snapshot.
	# Transpose this image according the settings and returns it
	# :return:
	def get_snapshot(self):
		# 1) Get the snapshot url if set and other webcam settings
		self._logger.info("Getting Snapshot")
		snapshot_url = self._settings.global_get(["webcam", "snapshot"])
		hflip = self._settings.global_get(["webcam", "flipH"])
		vflip = self._settings.global_get(["webcam", "flipV"])
		rotate = self._settings.global_get(["webcam", "rotate90"])
		self._logger.info("Snapshot URL: " + str(snapshot_url))
		if type(snapshot_url) is not str:
			return None

		# 2) Get the image data from the snapshot url
		image = None
		try:
			# Reduce the resolution of image to prevent 400 error when uploading content
			# Besides this saves network bandwidth and Android device or WearOS
			# cannot tell the difference in resolution
			image = requests.get(snapshot_url, stream=True).content
			image_obj = Image.open(BytesIO(image))

			# 3) Now resize the image so that it isn't too big to send.
			x, y = image_obj.size
			if x > 1640 or y > 1232:
				size = 1640, 1232
				image_obj.thumbnail(size, Image.ANTIALIAS)
				output = BytesIO()
				image_obj.save(output, format="JPEG")
				image = output.getvalue()
				output.close()
		except requests.exceptions.RequestException as e:
			self._logger.info("Error getting snapshot: " + str(e))
			return None
		except Exception as e:
			self._logger.info("Error reducing resolution of image: " + str(e))
			return None

		# 4) Flip or rotate the image if necessary
		if hflip or vflip or rotate:
			try:
				# https://www.blog.pythonlibrary.org/2017/10/05/how-to-rotate-mirror-photos-with-python/
				image_obj = Image.open(BytesIO(image))
				if hflip:
					image_obj = image_obj.transpose(Image.FLIP_LEFT_RIGHT)
				if vflip:
					image_obj = image_obj.transpose(Image.FLIP_TOP_BOTTOM)
				if rotate:
					image_obj = image_obj.rotate(90)

				# https://stackoverflow.com/questions/646286/python-pil-how-to-write-png-image-to-string/5504072
				output = BytesIO()
				image_obj.save(output, format="JPEG")
				image = output.getvalue()
				output.close()
			except Exception as e:
				self._logger.info("Error rotating image: " + str(e))
				return None
		return image


__plugin_name__ = "Webhooks"
__plugin_pythoncompat__ = ">=2.7,<4"


def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = WebhooksPlugin()
	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.gcode.received": __plugin_implementation__.recv_callback,
		"octoprint.events.register_custom_events": __plugin_implementation__.register_custom_events
	}
