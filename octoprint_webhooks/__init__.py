# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import requests

import octoprint.plugin
from octoprint.events import eventManager, Events


# Replaces any v in data that start with @param
# with the v in values. For instance, if data
# was {"abc":"@p1"}, and values was {"p1":"123"},
# then @p1 would get replaced with 123 like so:
# {"abc":"123"}
def replace_dict_with_data(d, v):
	for key in d:
		value = d[key]
		start_index = value.find("@")
		if start_index >= 0:
			# Find the end text by space
			end_index = value.find(" ", start_index)
			if end_index == -1:
				end_index = len(value)
			value_key = value[start_index + 1:end_index]
			if value_key in v:
				if start_index == 0 and end_index == len(value):
					d[key] = v[value_key]
				else:
					d[key] = d[key].replace(value[start_index:end_index], v[value_key])
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
			self._logger.info("API testhook CALLED!")
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

	def on_event(self, event, payload):
		topic = "Unknown"
		message = "Unknown"
		extra = payload

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
		if topic == "Unknown":
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
						self._logger.info("oauth headers: " + json.dumps(oauth_headers) + " - data: " + json.dumps(oauth_data))
						self._logger.info("oauth_http_method: " + oauth_http_method + " - oauth_content_type: " + oauth_content_type)
						response = requests.request(oauth_http_method, oauth_url, json=oauth_data, headers=oauth_headers)
					else:
						# Make sure the Content-Type header is set to application/x-www-form-urlencoded
						oauth_headers = check_for_header(oauth_headers, "content-type", "application/x-www-form-urlencoded")
						self._logger.info("oauth headers: " + json.dumps(oauth_headers) + " - data: " + json.dumps(oauth_data))
						self._logger.info("oauth_http_method: " + oauth_http_method + " - oauth_content_type: " + oauth_content_type)
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
		parsed_headers = False
		try:
			url = self._settings.get(["url"])
			api_secret = self._settings.get(["apiSecret"])
			device_identifier = self._settings.get(["deviceIdentifier"])
			headers = json.loads(self._settings.get(["headers"]))
			parsed_headers = True
			data = json.loads(self._settings.get(["data"]))
			http_method = self._settings.get(["http_method"])
			content_type = self._settings.get(["content_type"])
			# 2.1) Create a dictionary of all possible replacement variables.
			values = {
				"topic": topic,
				"message": message,
				"apiSecret": api_secret,
				"deviceIdentifier": device_identifier,
				"extra": extra
			}
			# 2.2) Merge these values with the oauth values.
			values.update(oauth_result)
			# 2.3) Replace the data and header elements that start with @
			data = replace_dict_with_data(data, values)
			headers = replace_dict_with_data(headers, values)
			# 2.4) Send the request
			response = ""
			if http_method == "GET":
				response = requests.get(url, params=data, headers=headers)
			else:
				if content_type == "JSON":
					# Make sure the Content-Type header is set to application/json
					headers = check_for_header(headers, "content-type", "application/json")
					self._logger.info("headers: " + json.dumps(headers) + " - data: " + json.dumps(data) + " - values: " + json.dumps(values))
					self._logger.info("http_method: " + http_method + " - content_type: " + content_type)
					response = requests.request(http_method, url, json=data, headers=headers)
				else:
					# Make sure the Content-Type header is set to application/x-www-form-urlencoded
					headers = check_for_header(headers, "content-type", "application/x-www-form-urlencoded")
					self._logger.info("headers: " + json.dumps(headers) + " - data: " + json.dumps(data) + " - values: " + json.dumps(values))
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
			if parsed_headers:
				self._logger.info("JSON Parse DATA Issue: " + str(e))
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", msg="Invalid JSON for Webhooks DATA Setting"))
			else:
				self._logger.info("JSON Parse HEADERS Issue: " + str(e))
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="error", msg="Invalid JSON for Webhooks HEADERS Setting"))

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
