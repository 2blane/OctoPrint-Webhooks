$(function() {
    function WebhookSettingsCustomViewModel(parameters) {
        var self = this
        self.settings = parameters[0]
        self.hooks = ko.observableArray();
        self.selectedHook = ko.observable();
        self.selectedIndex = ko.observable(-1);

        //Section folding
        self.foldTemplates = ko.observable(true)
        self.foldWebhookParameters = ko.observable(true)
        self.foldEvents = ko.observable(true)
        self.foldAdvanced = ko.observable(true)
        self.foldOAuth = ko.observable(true)

        //Templating
        self.availableTemplates = ko.observableArray() // the list of available templates for the selection list
        self.template = ko.observable({"_description": "no description"}) // the selected template
        self.templateData = ko.observable("") // the data to download for the current settings state. Used to create a template JSON file.

        self.templateActivated = ko.observable(false) // has the template been activated?
        self.templateDescription = ko.observable("no description") //the selected template's description

        self.onStartup = function() {
            console.log("WebhookSettingsCustomViewModel startup")
        }

        self.onBeforeBinding = function() {
            self.hooks(self.settings.settings.plugins.webhooks.hooks())
            //Select the first hook. There should always be a selected hook.
            self.selectHook(0)
            //Get the list of available templates.
            let templates = ["simple.json", "fulldata.json", "snapshot.json", "oauth.json", "dotnotation.json"]
            let callbacksLeft = templates.length;
            for (let i = 0; i < templates.length; i = i + 1) {
                let templateFile = "plugin/webhooks/static/templates/" + templates[i]
                $.getJSON(templateFile, function(data) {
                    console.log("json file: ", data)
                    self.availableTemplates.push(data)
                    console.log("available templates: ", self.availableTemplates())
                    callbacksLeft -= 1;
                    if (callbacksLeft == 0) {
                        self.template(self.availableTemplates()[0])
                        console.log("selected template: ", self.template())
                    }
                })
            }
        }

        self.templateChanged = function(data) {
            self.templateActivated(false)
            self.templateDescription(self.template()["_description"])
        }

        self.activateTemplate = function() {
            console.log(self.template())
            self.templateActivated(true)
            //Loop over keys in the template and set only those keys in the template on the current hook.
            let td = self.template()
            let data = self.selectedHook()
            for (let prop in td) {
                if (prop in data) {
                    console.log("setting prop", prop, td[prop])
                    self.selectedHook()[prop](td[prop])
                }
            }
        }

        self.downloadTemplate = function() {
            let data = ko.toJS(self.selectedHook())
            console.log("download a template: ", data)
            delete data["url"]
            delete data["apiSecret"]
            delete data["deviceIdentifier"]
            delete data["webhook_enabled"]
            delete data["test_event"]
            delete data["eventPrintStarted"]
            delete data["eventPrintDone"]
            delete data["eventPrintFailed"]
            delete data["eventPrintPaused"]
            delete data["eventUserActionNeeded"]
            delete data["eventError"]
            delete data["event_print_progress"]
            delete data["__ko_mapping__"]
            if (data["oauth"] == false) {
                delete data["oauth_url"]
                delete data["oauth_headers"]
                delete data["oauth_data"]
                delete data["oauth_http_method"]
                delete data["oauth_content_type"]
            }
            data["_name"] = "TODO: FILL THIS OUT. SHOULD BE LESS THAN 30 CHARACTERS. WILL SHOW UP IN THE TEMPLATE SELECT BOX. SOMETHING LIKE 'Slack Message - v1'."
            data["_description"] = "TODO: FILL THIS OUT. THIS WILL SHOW WHEN YOUR TEMPLATE HAS BEEN SELECTED. SHOULD EXPLAIN WHAT THE TEMPLATE IS, HOW TO USE IT, AND ANYTHING ELSE NECESSARY."
            self.templateData("data:application/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data)))
            document.getElementById("templateDownloadA").click()
        }

        self.foldSection = function(section) {
            console.log("foldSection: ", section)
            if (section == "templates") {
                self.foldTemplates(!self.foldTemplates())
            } else if (section == "webhookParameters") {
                self.foldWebhookParameters(!self.foldWebhookParameters())
            } else if (section == "events") {
                self.foldEvents(!self.foldEvents())
            } else if (section == "advanced") {
                self.foldAdvanced(!self.foldAdvanced())
            } else if (section == "oAuth") {
                self.foldOAuth(!self.foldOAuth())
            }
        }

        self.eventListText = function(data) {
            console.log("eventListText", data)
            return "No Events"
        }

        self.selectHook = function(index) {
            if (self.hooks().length > index) {
                self.selectedIndex(index)
                self.selectedHook(self.settings.settings.plugins.webhooks.hooks()[index])
                //console.log("HOOKS", self.hooks(), self.hooks()[index])
                //console.log("SELECTED HOOK IS SET", self.selectedHook())
            } else if (self.hooks().length > 0) {
                self.selectHook(0)
            } else {
                self.selectedIndex(-1)
            }
        }

        self.editHook = function(index) {
            //console.log("Edit Hook", index)
            self.selectHook(index)
        }

        self.removeHook = function(data) {
            //console.log("Remove Hook", data)
            self.settings.settings.plugins.webhooks.hooks.remove(data)
            self.selectHook(0)
        }

        self.copyHook = function(data) {
            console.log("Copy Hook", data)
            self.selectedHook(ko.mapping.fromJS(ko.toJS(data)))
            self.settings.settings.plugins.webhooks.hooks.push(self.selectedHook())
            self.selectedIndex(self.settings.settings.plugins.webhooks.hooks().length - 1)
        }

        self.newHook = function() {
            self.selectedHook({
                'url': ko.observable(''),
                'apiSecret': ko.observable(''),
                'deviceIdentifier': ko.observable(''),
                'webhook_enabled': ko.observable(true),

                'eventPrintStarted': ko.observable(true),
                'eventPrintDone': ko.observable(true),
                'eventPrintFailed': ko.observable(true),
                'eventPrintPaused': ko.observable(true),
                'eventUserActionNeeded': ko.observable(true),
                'eventError': ko.observable(true),
                'event_print_progress': ko.observable(false),
                'event_print_progress_interval': ko.observable("50"),

                'eventPrintStartedMessage': ko.observable("Your print has started"),
                'eventPrintDoneMessage': ko.observable("Your print is done."),
                'eventPrintFailedMessage': ko.observable("Something went wrong and your print has failed."),
                'eventPrintPausedMessage': ko.observable("Your print has paused. You might need to change the filament color."),
                'eventUserActionNeededMessage': ko.observable("User action needed. You might need to change the filament color."),
                'eventPrintProgressMessage': ko.observable("Your print is @percentCompleteMilestone % complete."),
                'eventErrorMessage': ko.observable("There was an error."),

                'headers': ko.observable('{\n  "Content-Type": "application/json"\n}'),
                'data': ko.observable('{\n  "deviceIdentifier":"@deviceIdentifier",\n  "apiSecret":"@apiSecret",\n  "topic":"@topic",\n  "message":"@message",\n  "extra":"@extra",\n  "state": "@state",\n  "job": "@job",\n  "progress": "@progress",\n  "currentZ": "@currentZ",\n  "offsets": "@offsets",\n  "meta": "@meta",\n  "currentTime": "@currentTime",\n  "snapshot": "@snapshot"\n}'),
                'http_method': ko.observable("POST"),
                'content_type': ko.observable("JSON"),
                'oauth': ko.observable(false),
                'oauth_url': ko.observable(""),
                'oauth_headers': ko.observable('{\n  "Content-Type": "application/json"\n}'),
                'oauth_data': ko.observable('{\n  "client_id":"myClient",\n  "client_secret":"mySecret",\n  "grant_type":"client_credentials"\n}'),
                'oauth_http_method': ko.observable("POST"),
                'oauth_content_type': ko.observable("JSON"),
                'test_event': ko.observable("PrintStarted"),
            })
            self.settings.settings.plugins.webhooks.hooks.push(self.selectedHook())
            self.selectedIndex(self.settings.settings.plugins.webhooks.hooks().length - 1)
        }

        self.resetDataToDefaults = function() {
            // Update the data to be defaulted.
            self.settings.settings.plugins.webhooks.data('{\n  "deviceIdentifier":"@deviceIdentifier",\n  "apiSecret":"@apiSecret",\n  "topic":"@topic",\n  "message":"@message",\n  "extra":"@extra",\n  "state": "@state",\n  "job": "@job",\n  "progress": "@progress",\n  "currentZ": "@currentZ",\n  "offsets": "@offsets",\n  "meta": "@meta",\n  "currentTime": "@currentTime",\n  "snapshot": "@snapshot"\n}')
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
                    client.postJson("api/plugin/webhooks", {"command":"testhook", "event":event, "hook_index": self.selectedIndex()})
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
