#! /usr/bin/env python
"""
Turn on some lights when the ISS passes overhead
"""
from datetime import datetime
import requests
import sys
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
# from phue import Bridge


class IssLightAlarm():

    def __init__(self, config='./iss_light_alarm.yaml'):
        try:
            with open(config, 'r') as fptr:
                configs = yaml.load(fptr.read())
                self._latitude = configs['location']['latitude']
                self._longitude = configs['location']['longitude']
                # self._bridge_ip = configs['hue']['bridgeip']
        except IOError as e:
            print("Unalbe to load configuration: {0}".format(e))
            sys.exit(1)
        self._scheduler = BackgroundScheduler()
        self._scheduler.start()
        # self._bridge = Bridge(self._bridge_ip)
        # self._bridge.connect()
        # self._lightid = 4
        # self._light = self._bridge.get_light(self._lightid)

    def run_light_sequence(self):
        pass

    def request_next_pass(self):
        """Check for the next time the ISS will fly over the specified coordinates
        """
        url = "http://api.open-notify.org/iss-pass.json?lat={0}&lon={1}"
        url = url.format(self._latitude, self._longitude)
        print(url)
        try:
            data = requests.get(url)
        except Exception as e:
            print('Unable to request from url "{0}" because {1}'.format(
                url, e))
            sys.exit(1)
        if data.status_code / 100 != 2:
            print("{0} response: {1}".format(data.status_code, data.text))
        api_response = data.json()
        if (api_response['message'] == "success"):
            next_risetime = api_response['response'][0]['risetime']
            next_duration = api_response['response'][0]['duration']
            print("Next ISS overflight at {0}, lasting {1} seconds".format(
                datetime.fromtimestamp(next_risetime), next_duration))


if __name__ == '__main__':
    isslamp = IssLightAlarm()
    isslamp.request_next_pass()
