$(function() {
    function WebhookSettingsCustomViewModel(parameters) {
        var self = this
        self.settings = parameters[0]

        self.resetDataToDefaults = function() {
            // Update the data to be defaulted.
            self.settings.settings.plugins.webhooks.data('{\n  "deviceIdentifier":"@deviceIdentifier",\n  "apiSecret":"@apiSecret",\n  "topic":"@topic",\n  "message":"@message",\n  "extra":"@extra"\n}')
            console.log("Webhooks Reset DATA to Defaults Pressed")
        }

        self.resetHeadersToDefaults = function() {
            // Update the data to be defaulted.
            self.settings.settings.plugins.webhooks.headers('{\n  "Content-Type": "application/json"\n}')
            console.log("Webhooks Reset HEADERS to Defaults Pressed")
        }

        self.resetOAuthDataToDefaults = function() {
            // Update the data to be defaulted.
            self.settings.settings.plugins.webhooks.oauth_data('{\n  "client_id":"myClient",\n  "client_secret":"mySecret",\n  "grant_type":"client_credentials"\n}')
            console.log("Webhooks Reset OAUTH_DATA to Defaults Pressed")
        }

        self.resetOAuthHeadersToDefaults = function() {
            // Update the data to be defaulted.
            self.settings.settings.plugins.webhooks.oauth_headers('{\n  "Content-Type": "application/json"\n}')
            console.log("Webhooks Reset OAUTH_HEADERS to Defaults Pressed")
        }

        self.onStartup = function() {
            console.log("WebhookSettingsCustomViewModel startup")
        }

        self.onDataUpdaterPluginMessage = function(plugin, data) {
            if (plugin != "webhooks") {
				console.log('PLUGS - Ignoring '+plugin);
                return;
            }
            hide = true
            if (data["hide"] !== undefined) {
                hide = data["hide"]
            }
			new PNotify({
			    title: 'Webhooks',
                text: data.msg,
                type: data.type,
			    hide: hide
			});
		}

        self.testWebhook = function(data) {
            var client = new OctoPrintClient()
            client.options.baseurl = "/"
            // 1) Save the user settings.
            data = ko.mapping.toJS(self.settings.settings.plugins.webhooks);
            console.log("WEBHOOKS - ", data)
            return OctoPrint.settings.savePluginSettings("webhooks", data)
                .done(function(data, status, xhr) {
                    //saved
                    console.log("settings saved")
                    // 2) Send a test event to the python backend.
                    event = self.settings.settings.plugins.webhooks.test_event()
                    client.postJson("api/plugin/webhooks", {"command":"testhook", "event":event})
                })
                .fail(function(xhr, status, error) {
                    //failed to save
                    console.log("failed to save settings")
                })
		}
    }

    OCTOPRINT_VIEWMODELS.push([
        WebhookSettingsCustomViewModel,
        ["settingsViewModel"],
        ["#settings_plugin_webhooks"]
    ])
})
