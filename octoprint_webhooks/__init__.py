# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import json
import requests

import octoprint.plugin
from octoprint.events import eventManager, Events


class WebhooksPlugin(octoprint.plugin.StartupPlugin, octoprint.plugin.TemplatePlugin, octoprint.plugin.SettingsPlugin,
					 octoprint.plugin.EventHandlerPlugin):
	def __init__(self):
		self.triggered = False

	def on_after_startup(self):
		self._logger.info("Hello World from WebhooksPlugin! " + self._settings.get(["url"]))

	def get_settings_defaults(self):
		return dict(url="https://www.darwincloud.com", apiSecret="abcd1234", deviceIdentifier="Printer1")

	def get_template_configs(self):
		return [
			dict(type="navbar", custom_bindings=False),
			dict(type="settings", custom_bindings=False)
		]

	def register_custom_events(self, *args, **kwargs):
		return ["notify"]

	def on_event(self, event, payload):
		topic = "Unknown"
		message = "Unknown"
		extra = payload

		if event == Events.PRINT_STARTED:
			topic = "Print Started"
			message = "Your print has started."
		elif event == Events.PRINT_DONE:
			topic = "Print Done"
			message = "Your print is done."
		elif event == Events.PRINT_FAILED:
			topic = "Print Failed"
			message = "Something went wrong and your print has failed."
		elif event == Events.PRINT_PAUSED:
			topic = "Print Paused"
			message = "Your print has paused. You might need to change the filament color."
		elif event == Events.PLUGIN_WEBHOOKS_NOTIFY:
			topic = "User Action Needed"
			message = "User action is needed. You might need to change the filament color."
		elif event == Events.ERROR:
			topic = "Error"
			message = "There was an error."
		if topic == "Unknown":
			return
		self._logger.info("P EVENT " + topic + " - " + message)
		# Send the notification
		# 1) Call the API
		try:
			url = self._settings.get(["url"])
			apiSecret = self._settings.get(["apiSecret"])
			deviceIdentifier = self._settings.get(["deviceIdentifier"])
			headers = {}
			values = {
				"deviceIdentifier": deviceIdentifier,
				"apiSecret": apiSecret,
				"topic": topic,
				"message": message,
				"extra": extra
			}
			response = requests.post(url, data=values)
			result = json.loads(response.text)
			self._logger.info("API SUCCESS: " + event + " " + json.dumps(result))
		except requests.exceptions.RequestException as e:
			self._logger.info("API ERROR" + str(e))

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
		# "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
		"octoprint.comm.protocol.gcode.received": __plugin_implementation__.recv_callback,
		"octoprint.events.register_custom_events": __plugin_implementation__.register_custom_events
	}
