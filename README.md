# OctoPrint-Webhooks

This allows you to send a webhook to any URL when events happen on OctoPrint.

1. Change

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/2blane/OctoPrint-Webhooks/archive/master.zip

Once you've installed the plugin, go to the settings page for this plugin. The page is called "webhooks".
Change the following:

### URL
The url that will be called when events occur such as https://www.myapi.com/v1/method
### API SECRET
A secret that will be passed along in the API request that can be used to verify the webhook is coming from your OctoPrint Server. Set this to some random string and check in your API that the random string matches.
### DEVICE IDENTIFIER
A name or id that you can provide to your printer to distinguish printers from each other.

## Webhook Request
The webhook will be called as a POST request with the following data:
```
{
  deviceIdentifier: "the DEVICE IDENTIFIER in settings"
  apiSecret: "the API SECRET in settings"
  topic: "the name of the event - see below for events"
  message: "a description of the event - can be used for display purposes"
  extra: {...} //a json object of data related to the event - different for each event
}
```

## Events

* Print Started
The print has started.
* Print Done
The print has finished.
* Print Failed
The print has failed.
* Print Paused
The print has been paused.
* User Action Needed
Called on Prusa Printers when a color change is necessary.
* Error
An error has occurred. Can refer to many different types of errors.

## Event Data
For details on what 'extra' data is provided with each event, check out the following.
https://docs.octoprint.org/en/master/events/index.html#printing
