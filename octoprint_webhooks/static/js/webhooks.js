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

        self.onStartup = function() {
            console.log("WebhookSettingsCustomViewModel startup")
        }
    }

    OCTOPRINT_VIEWMODELS.push([
        WebhookSettingsCustomViewModel,
        ["settingsViewModel"],
        ["#settings_plugin_webhooks"]
    ])
})
