#! /usr/bin/env python
"""
Turn on some lights when the ISS passes overhead
"""
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from phue import Bridge
import requests
import sys
import time
import yaml


class IssLightAlarm():

    def __init__(self, config='./iss_light_alarm.yaml'):
        try:
            with open(config, 'r') as fptr:
                configs = yaml.load(fptr.read())
                self._latitude = configs['location']['latitude']
                self._longitude = configs['location']['longitude']
                self._bridge_ip = configs['hue']['bridgeip']
        except IOError as e:
            print("Unalbe to load configuration: {0}".format(e))
            sys.exit(1)
        self._scheduler = BackgroundScheduler()
        self._scheduler.start()
        self._bridge = Bridge(self._bridge_ip)
        self._bridge.connect()
        self._lightid = 4
        self._light = self._bridge.get_light(self._lightid)

    def end_light_sequence(self):
        """Helper method to turn off the lights"""
        self._bridge.set_light(self._lightid, {'on': False})

    def run_light_sequence(self, duration):
        """This is one start-to-finish sequence of turning the lights on
        when the ISS is above 10 degrees in elevation from the provided
        coordinates and then turning the lights off when the ISS is no
        longer above 10 degrees in elevation."""
        # turn the light on
        self._bridge.set_light(self._lightid,
                               {'on': True})
        # schedule to turn the light off in -duration- seconds
        # TODO we should do this before we turn the light on
        # because it might take a few seconds to talk to the Hue bridge
        stop_time = datetime.now() + timedelta(seconds=duration)
        print(stop_time)
        self._scheduler.add_job(self.end_light_sequence, 'date',
                                run_date=stop_time)
        # start the loop again by requesting the next pass
        self._scheduler.add_job(self.request_next_pass, 'date',
                                run_date=stop_time)

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
            self._scheduler.add_job(self.run_light_sequence(next_duration),
                                    'date',
                                    run_date=datetime.fromtimestamp(
                                        next_risetime))


if __name__ == '__main__':
    isslamp = IssLightAlarm()
    isslamp.request_next_pass()
    try:
        while True:
            time.sleep(2)
    except (KeyboardInterrupt, SystemExit):
        isslamp.scheduler.shutdown()
