# OctoPrint-Webhooks

This allows you to send a webhook (a.k.a. API Request) to any URL when events happen on OctoPrint such as when
a print finishes, fails, ...

## [Blog Post](https://www.darwincloud.com/blog/add-webhooks-to-your-3d-printer-with-octoprint/)

I wrote a blog post to explain more about what this plugin is and why I built it.

## Setup

Install via the bundled [Plugin Manager](https://docs.octoprint.org/en/master/bundledplugins/pluginmanager.html)
or manually using this URL:

    https://github.com/2blane/OctoPrint-Webhooks/archive/master.zip

Once you've installed the plugin, go to the settings page for this plugin. The page is called "Webhooks".
Change the following:

#### URL
The url that will be called when events occur such as https://www.myapi.com/v1/method
#### API SECRET
A secret that will be passed along in the API request that can be used to verify the webhook is coming from your OctoPrint Server. Set this to some random string and check in your API that the random string matches.
#### DEVICE IDENTIFIER
A name or id that you can provide to your printer to distinguish printers from each other.

## Webhook Request
By default, the webhook will be called as a POST request with the following data:
```
{
  "deviceIdentifier": "the DEVICE IDENTIFIER in settings",
  "apiSecret": "the API SECRET in settings",
  "topic": "the name of the event - see below for events",
  "message": "a description of the event - can be used for display purposes",
  "extra": {...} //a json object of data related to the event - different for each event
}
```

To change the format of the request, there are some advanced configuration parameters you can modify.

## Advanced Configuration

#### Headers
Provide a JSON dictionary of headers that will be passed along with the request such as:
```
{
  "Content-Type": "application/json"
}
```

#### Data
Provide a JSON dictionary of parameters that will be passed along with the request such as:
```
{
  "deviceIdentifier":"@deviceIdentifier",
  "apiSecret":"@apiSecret",
  "topic":"@topic",
  "message":"@message",
  "extra":"@extra",
  "custom1":"my custom data",
  "custom2":"my second piece of custom data"
}
```

*** NOTE - any word that starts with an @ symbol will be replaced if possible by variables.
For instance, in the above JSON: @message will be replaced with the real message that triggered the webhook.
Below is a list of variables you can use in your request.

#### Available Variables
@deviceIdentifier - the user set DEVICE IDENTIFIER found in settings

@apiSecret - the user set API SECRET found in settings

@topic - the type of event that was triggered. See below for a list of topics/events.

@message - a short description of the type of event that was triggered.

@extra - a dictionary of extra data that was passed along by OctoPrint.


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
