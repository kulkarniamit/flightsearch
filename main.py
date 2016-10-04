#!/usr/bin/env python2.7
import requests
import argparse
import logging
import json
from time import gmtime, strftime
from slack_api import SlackIncomingWebhookAPI

try:
    import httplib
except ImportError:
    import http.client as httplib

parser = argparse.ArgumentParser(description='studentuniverse flight search',add_help=True)
parser.add_argument('-s', '--source', type=str, default="BOS", help='Airport code of departure city', required=False)
parser.add_argument('-d', '--destination', type=str, default="BLR", help='Airport code of destination city', required=False)
parser.add_argument('-f', action="store_true", default=False, help='Turn on flexible dates')
parser.add_argument('-D', action="store_true", default=False, help='Turn on debugging')
parser.add_argument('--version', action='version', version='%(prog)s 1.1')

required_args = parser.add_argument_group('Required named arguments')
required_args.add_argument('-l', '--leave', type=str, help='Departure date in format YYYY-MM-DD', required=True)
required_args.add_argument('-r', '--returndate', type=str, help='Return date in format YYYY-MM-DD', required=True)

results = parser.parse_args()

requested_source_airport = results.source
requested_destination_airport = results.destination
requested_departure_date = results.leave
requested_return_date = results.returndate
flexibility_flag = results.f
debug_flag = results.D
NUMBER_OF_CHEAPEST_DEALS = 5
SLACK_NOTIFICATION_FLAG = False
KEY_VALUE_PRINT_FORMAT = "{0:15}{1}"

class StudentUniverse(object):
    """Base class for constructing a studentuniverse flight search query
    Loads all settings and credentials from one 'settings.yaml' file
    and performs common OAuth2.0 related functionality such as authentication
    and authorization.
    """
    base_URL = "https://www.studentuniverse.com"
    host = "www.studentuniverse.com"
    # Endpoint to get results without flexible dates
    # flight_search_endpoint = "/wapi/flightsWapi/searchFlights"
    flight_search_endpoint = "/wapi/flightsWapi/searchFlightsSpanned"
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.116 Safari/537.36"
    index_request_headers = {
        "Host": host,
        "Connection": "keep-alive",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent":user_agent,
        "Accept": "text/html, application/xhtml+xml,application/xml; q = 0.9,image/webp,*/*;q=0.8",
        "DNT": "1",
        "Accept-Encoding": "gzip,deflate,sdch,br",
        "Accept-Language":"en-US,en;q=0.8,ms;q=0.6"
    }
    flight_search_headers = {
        "Host": host,
        "Connection": "keep-alive",
        "Content-Length": "277",
        "Accept": "application/json, text/plain, */*",
        "Su-Fail-If-First": "true",
        "Origin": "https://www.studentuniverse.com",
        "User-Agent": user_agent,
        "Content-Type": "text/plain",
        "DNT": "1",
        "Referer": "https://www.studentuniverse.com/",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.8,ms;q=0.6"
    }

    @staticmethod
    def get_human_readable_duration(minutes):
        hours = (minutes/60.00)
        int_hours = int(hours)
        minutes = int((hours-int_hours)*60)
        return str(int_hours)+"h "+str(minutes)+"m"

    @staticmethod
    def get_flight_carriers(flight_segments):
        carriers = [flight['carrierCode'] for flight in flight_segments]
        return carriers

    @staticmethod
    def read_airline_codes():
        airline_codes = {}
        with open("airlinecodes.txt") as lines:
            # Courtesy: http://www.avrefdesk.com/two_letter_airline_codes.htm
            for line in lines:
                airline_name, airline_code = line.rsplit("\t")
                airline_codes[airline_code.strip()] = airline_name
        return airline_codes

    def __init__(self, src, dst, dep_date, ret_date, flexibility=False, debug=False):
        self.from_city = src
        self.to_city = dst
        self.departure_date = dep_date
        self.return_date = ret_date
        self.flexible_date = flexibility
        if debug:
            httplib.HTTPConnection.debuglevel = 1
            logging.basicConfig()
            logging.getLogger().setLevel(logging.DEBUG)
            requests_log = logging.getLogger("requests.packages.urllib3")
            requests_log.setLevel(logging.DEBUG)
            requests_log.propagate = True
        self.flight_search_response_code = 0
        self.cookies = self.get_cookies()
        self.flight_itineraries = {}
        self.flight_summary_info = {}
        self.flight_lowfares = {}
        self.airline_codes = self.read_airline_codes()

    def get_origin(self):
        return self.from_city

    def get_destination(self):
        return self.to_city

    def get_departure_date(self):
        return self.departure_date

    def get_return_data(self):
        return self.return_date

    def get_flexibility(self):
        return self.flexible_date

    def get_index_payload(self):
        return self.index_request_headers

    def get_search_headers(self):
        return self.flight_search_headers

    def get_search_payload(self):
        payload = {"tripElements":[
                    {
                        "origin":self.from_city,
                        "destination":self.to_city,
                        "dateTime":self.departure_date+"T00:00:00"
                    },
                    {
                        "origin": self.to_city,
                        "destination": self.from_city,
                        "dateTime": self.return_date+"T00:00:00"
                    }],
                   "numberOfPassengers":"1",
                   "details":"false",
                   "searchStartTime":strftime("%Y-%m-%dT%H:%M:%S"),
                   "source":"urlSearch",
                   "searchKey":"null"
                   }
        return payload

    def get_cookies(self):
        index_response = requests.get(self.base_URL, headers=self.get_index_payload())
        cookies = requests.utils.dict_from_cookiejar(index_response.cookies)
        return cookies

    def search_cheapest_flight(self):
        flight_search_URL = self.base_URL + self.flight_search_endpoint
        # Need to convert this, otherwise payload is not recognized by server
        flight_search_payload_json = json.dumps(self.get_search_payload())
        flight_search_results = requests.post(flight_search_URL, data=flight_search_payload_json,
                                              cookies=self.cookies,
                                              headers=self.get_search_headers())
        self.flight_search_response_code = flight_search_results.status_code
        flight_search_data = flight_search_results.json()

        #   Here's some information about itineraries and lowFares
        #   itineraries contain fixed date prices (sorted in ascending order)
        #   lowFares contain flexible dates with cheapest prices

        self.flight_itineraries = flight_search_data['itineraries']
        self.flight_summary_info = flight_search_data['summaryInfo']
        self.flight_lowfares = flight_search_data['lowFares']

    def get_flight_fixed_date(self):
        # This is the cheapest for the FIXED DATE and not the flexible dates
        return "$"+str(self.flight_summary_info['cheapestItinerary']['price'])

    def get_cheap_flight_details(self):
        # These are the cheapest details for the FIXED DATE and not the flexible dates

        fixed_date_flight_data = {
            'onward_departure_date': self.flight_itineraries[0]['legs'][0]['departureTime'],
            'onward_arrival_date': self.flight_itineraries[0]['legs'][0]['arrivalTime'],
            'return_departure_date': self.flight_itineraries[0]['legs'][1]['departureTime'],
            'return_arrival_date': self.flight_itineraries[0]['legs'][1]['arrivalTime'],
            'onward_journey_time': self.get_human_readable_duration(self.flight_itineraries[0]['legs'][0]['duration']),
            'return_journey_time': self.get_human_readable_duration(self.flight_itineraries[0]['legs'][1]['duration']),
            'onward_carriers': self.get_flight_carriers(self.flight_itineraries[0]['legs'][0]['flightSegments']),
            'return_carriers': self.get_flight_carriers(self.flight_itineraries[0]['legs'][1]['flightSegments'])
        }
        return fixed_date_flight_data

    def get_flexible_results(self, su_data):
        cheapest_flight_deals = sorted(self.flight_lowfares,key=lambda x:x['total'])[:NUMBER_OF_CHEAPEST_DEALS]
        su_data.append("Top " + str(NUMBER_OF_CHEAPEST_DEALS) + " cheapest deals if you are flexible with dates:")
        su_data.append("---------------------------------------------")
        for deal in cheapest_flight_deals:
            su_data.append(KEY_VALUE_PRINT_FORMAT.format("Price:","$"+str(deal['total'])))
            su_data.append(KEY_VALUE_PRINT_FORMAT.format("Departure:",str(deal['dates']['outbound'][:10])))
            su_data.append(KEY_VALUE_PRINT_FORMAT.format("Return:", str(deal['dates']['inbound'][:10])))
            su_data.append("---------------------------------------------")

if __name__ == "__main__":
    su_result = StudentUniverse(requested_source_airport,
                                requested_destination_airport,
                                requested_departure_date,
                                requested_return_date,
                                flexibility_flag,
                                debug_flag)
    su_result.search_cheapest_flight()
    if su_result.flight_search_response_code == 200:
        su_data = []
        if flexibility_flag:
            # User is requesting flexible date flights, show them results
            su_result.get_flexible_results(su_data)
        fixed_date_flight = su_result.get_cheap_flight_details()
        onward_carriers = [su_result.airline_codes[airlinecode] for airlinecode in fixed_date_flight['onward_carriers']]
        return_carriers = [su_result.airline_codes[airlinecode] for airlinecode in fixed_date_flight['return_carriers']]

        su_data.append(" ")
        su_data.append("Cheapest flight price of selected date: " + su_result.get_flight_fixed_date())
        su_data.append("---------------------------------------------------------")
        su_data.append("Onward journey :-")
        su_data.append(KEY_VALUE_PRINT_FORMAT.format("Departure:", fixed_date_flight['onward_departure_date']))
        su_data.append(KEY_VALUE_PRINT_FORMAT.format("Arrival:", fixed_date_flight['onward_arrival_date']))
        su_data.append("---------------------------------------------------------")
        su_data.append("Return journey :-")
        su_data.append(KEY_VALUE_PRINT_FORMAT.format("Departure:", fixed_date_flight['return_departure_date']))
        su_data.append(KEY_VALUE_PRINT_FORMAT.format("Arrival:", fixed_date_flight['return_arrival_date']))
        su_data.append("---------------------------------------------------------")
        su_data.append(KEY_VALUE_PRINT_FORMAT.format("Onward time:", fixed_date_flight['onward_journey_time']))
        su_data.append(KEY_VALUE_PRINT_FORMAT.format("Return time:", fixed_date_flight['return_journey_time']))
        su_data.append(KEY_VALUE_PRINT_FORMAT.format("Onward Carriers:", str(onward_carriers)))
        su_data.append(KEY_VALUE_PRINT_FORMAT.format("Return Carriers:", str(return_carriers)))

        print "\n".join(su_data)
        if SLACK_NOTIFICATION_FLAG:
            slack_push_object = SlackIncomingWebhookAPI()
            slack_push_object.push_to_slack_channel(su_data)
    else:
        print "Unable to fetch response"
        print "Response code: "+str(su_result.flight_search_response_code)
        exit(1)
    exit(0)