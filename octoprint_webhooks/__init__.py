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
		if value[0:1] == "@":
			value_key = value[1:]
			if value_key in v:
				d[key] = v[value_key]
	return d


class WebhooksPlugin(octoprint.plugin.StartupPlugin, octoprint.plugin.TemplatePlugin, octoprint.plugin.SettingsPlugin,
					 octoprint.plugin.EventHandlerPlugin, octoprint.plugin.AssetPlugin):
	def __init__(self):
		self.triggered = False

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
					headers='{\n  "Content-Type": "application/json"\n}',
					data='{\n  "deviceIdentifier":"@deviceIdentifier",\n  "apiSecret":"@apiSecret",\n  "topic":"@topic",\n  "message":"@message",\n  "extra":"@extra"\n}'
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
		return ["notify"]

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
		elif event == Events.ERROR and self._settings.get(["eventError"]):
			topic = "Error"
			message = "There was an error."
		if topic == "Unknown":
			return
		self._logger.info("P EVENT " + topic + " - " + message)
		# Send the notification
		# 1) Call the API
		parsed_headers = False
		try:
			url = self._settings.get(["url"])
			api_secret = self._settings.get(["apiSecret"])
			device_identifier = self._settings.get(["deviceIdentifier"])
			headers = json.loads(self._settings.get(["headers"]))
			parsed_headers = True
			data = json.loads(self._settings.get(["data"]))
			# 1.1) Create a dictionary of all possible replacement variables.
			values = {
				"topic": topic,
				"message": message,
				"extra": extra,
				"apiSecret": api_secret,
				"deviceIdentifier": device_identifier
			}
			# 1.2) Replace the data and header elements that start with @
			data = replace_dict_with_data(data, values)
			headers = replace_dict_with_data(headers, values)
			# 1.3) Send the request
			print("headers: " + json.dumps(headers) + " - data: " + json.dumps(data))
			response = requests.post(url, json=data, headers=headers)
			result = json.loads(response.text)
			self._logger.info("API SUCCESS: " + event + " " + json.dumps(result))
		except requests.exceptions.RequestException as e:
			self._logger.info("API ERROR" + str(e))
		except Exception as e:
			if parsed_headers:
				self._logger.info("JSON Parse DATA Issue")
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="info", autoClose=False, msg="Invalid JSON for Webhooks HEADERS Setting"))
			else:
				self._logger.info("JSON Parse HEADERS Issue")
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="info", autoClose=False, msg="Invalid JSON for Webhooks DATA Setting"))

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
