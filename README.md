# flightsearch

Search for flights on StudentUniverse and get notifications on Slack with a trigger

```
$ python2.7 main.py -h
usage: main.py [-h] [-s SOURCE] [-d DESTINATION] [-f] [-D] [--version] -l
               LEAVE -r RETURNDATE

studentuniverse flight search

optional arguments:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Airport code of departure city
  -d DESTINATION, --destination DESTINATION
                        Airport code of destination city
  -f                    Turn on flexible dates
  -D                    Turn on debugging
  --version             show program's version number and exit

Required named arguments:
  -l LEAVE, --leave LEAVE
                        Departure date in format YYYY-MM-DD
  -r RETURNDATE, --returndate RETURNDATE
                        Return date in format YYYY-MM-DD
```
