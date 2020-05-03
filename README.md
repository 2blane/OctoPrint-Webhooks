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
Select which events you want to trigger a webhook, then change the following:

#### URL
The url that will be called when events occur such as https://www.myapi.com/v1/method
#### HTTP METHOD
The type of HTTP request to make. Usually this is POST.
#### CONTENT TYPE
This determines how the data is encoded before it is sent to your server. Usually, JSON
will work, but on some older systems x-www-form-urlencoded might be needed.

NOTE: The proper header will be set for 'Content-Type' if you don't supply one that allows
the data to be sent properly. For instance, if you set this setting to JSON, 'application/json'
must appear somewhere your 'Content-Type' header, and if not it will get replaced. So, you
could set it to 'application/json charset=utf8;' if you wanted to, but not 'application/yoyo'
as that would fail.
#### API SECRET
A secret that will be passed along in the API request that can be used to verify the webhook
is coming from your OctoPrint Server.
Set this to some random string and check in your API that the random string matches.
#### DEVICE IDENTIFIER
A name or id that you can provide to your printer to distinguish printers from each other.

## Webhook Request
By default, the webhook will be called with the following data:
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

*** NOTE - you can use @param to insert variables into the JSON for both the
Headers and Data. For instance, if above you set 'DEVICE IDENTIFIER' to "Blane's Printer",
then @deviceIdentifer will get replaced with "Blane's Printer" when the webhook request
is made. See below for the list of available variables that you can use.

#### Available Variables
@deviceIdentifier - the user set DEVICE IDENTIFIER found in settings

@apiSecret - the user set API SECRET found in settings

@topic - the type of event that was triggered. See below for a list of topics/events.

@message - a short description of the type of event that was triggered.

@extra - a dictionary of extra data that was passed along by OctoPrint.


## Events / Topics
The following is the list of topics that can trigger a webhook.

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

* Print Progress

Sends progress reports every 'x' percent where is x is defined by you.
For instance, you can send a progress webhook every 10%, 25%, or 7% if you wanted.
NOTE: 0% and 100% are not triggered by this event, use 'Print Started' and 'Print Done'
for those events.

## Event Data
For details on what 'extra' data is provided with each event, check out the following.
https://docs.octoprint.org/en/master/events/index.html#printing

## OAuth
OAuth is a common authentication mechanism used by many APIs.
If your server requires you to first make an API call trading credentials
for tokens so that you can use those tokens in your API request,
then OAuth should be enabled. You can then access the properties of the
OAuth response using something like @access_token in the DATA and HEADER settings for
your webhook request.

Once you've ticked the box to enable OAuth, you'll see some fields that you need to
fill out such as the url to call, the HTTP Method, Content-Type, Headers, and Data.
These work similar to the webhook settings, except you can't use the @param trick.

When an event triggers a webhook, this OAuth request will be called first (if enabled).
The response is expected to be JSON and will be parsed. All the keys in the JSON dictionary
will be available as @params that will be passed into the webhook request.
For instance, if the reponse of the OAuth request was
```
{
  "access_token": "abc123",
  "refresh_token": "efg456",
  "expires_in": 3600
}
```
then you could use @access_token, @refresh_token, and @expires_in inside the
'DATA' and 'HEADERS' Advanced Settings to pass them into your webhook request.

## TESTING
At the bottom of the settings page, you can simulate events to test out your API
and make sure everything is working. Just choose the event type and click the
'Send Test Webhook' button. You'll see a popup message showing you the result of the
webhook and if there were any errors. You'll be notified if there are any JSON parsing
issues with the settings you provided or any networking issues etc.
The API requests that are sent are expected to return HTTP status codes between 200
and 399. Anything outside of that range will be considered an error.
