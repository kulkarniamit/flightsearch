# flightsearch

Search for flights on StudentUniverse and get notifications on Slack with a trigger

```
$ python2.7 main.py -h
usage: main.py [-h] [-s SOURCE] [-d DESTINATION] [-f] [-D] [-j] [-t TRIGGER]
               [--version] -l LEAVE -r RETURNDATE

studentuniverse flight search

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Airport code of departure city
  -d DESTINATION, --destination DESTINATION
                        Airport code of destination city
  -f                    Turn on flexible dates
  -D                    Turn on debugging
  -j                    Run as cron job on openshift server
  -t TRIGGER, --trigger TRIGGER
                        Trigger price for slack notifications
  --version             show program's version number and exit

Required named arguments:
  -l LEAVE, --leave LEAVE
                        Departure date in format YYYY-MM-DD
  -r RETURNDATE, --returndate RETURNDATE
                        Return date in format YYYY-MM-DD

```

### Description
This python program can be used to check cheapest flights between a source and a destination on studentuniverse.com.
User can specify the source airport, destination airport, departure date, return date and flexibility of dates.
On setting a trigger price, the user can turn on notifications on a slack channel to receive hourly updates if the price of flight goes below the trigger price

#### Settings for Slack
Before turning on slack notifications, following settings need to be done:

slack_api.py:
```python 
    slack_bot_name = "<INSERT_BOTNAME>"
    slack_channel_name = "#<INSERT_CHANNEL_NAME>'"
    slack_incoming_webhook = "<INSERT_YOUR_INCOMING_WEBHOOK_URL>"
```
main.py
```python
SLACK_NOTIFICATION_FLAG = True
```

#### Slack notifications
To enable hourly notifications, create a cronjob with the required parameters 
