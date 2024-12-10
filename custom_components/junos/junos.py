''' Python Code for Communication with Junos OS devices.  This is taken mostly from pyecobee, so much credit to those contributors'''
import requests
import json
import os
import logging
from time import sleep

from requests.exceptions import RequestException
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger('junos')

NEXT_SCHEDULE = 1

class InvalidCredentials(Exception):
    """Raised when Junos REST API returns a code indicating invalid credentials."""

    pass

def config_from_file(filename, config=None):
    ''' Small configuration file management function'''
    if config:
        # We're writing configuration
        try:
            with open(filename, 'w') as fdesc:
                fdesc.write(json.dumps(config))
        except IOError as error:
            logger.exception(error)
            return False
        return True
    else:
        # We're reading config
        if os.path.isfile(filename):
            try:
                with open(filename, 'r') as fdesc:
                    return json.loads(fdesc.read())
            except IOError as error:
                return False
        else:
            return {}


class Junos(object):
    ''' Class for storing Junos Interface Sensors '''

    def __init__(self, config_filename=None, url=None, username=None, user_password=None, verify_tls=None, config=None):
        self.interfaces = list()
        self.skip_next = False
        self.serial_number = ""
        self.description = ""

        if config is None:
            self.file_based_config = True
            if config_filename is None:
                if (username is None) or (user_password is None):
                    logger.error("Error. No username or password was supplied.")
                    return
                if verify_tls is None:
                    verify_tls = True
                jsonconfig = {"URL": url, "USERNAME": username, "PASSWORD": user_password, "VERIFY": verify_tls}
                config_filename = 'junos.conf'
                config_from_file(config_filename, jsonconfig)
            config = config_from_file(config_filename)
        else:
            self.file_based_config = False
        if 'URL' in config:
            self.url = config['URL']
        else:
            logger.error("URL missing from config.")
        if 'USERNAME' in config:
            self.username = config['USERNAME']
        else:
            logger.error("URL missing from config.")
        if 'PASSWORD' in config:
            self.user_password = config['PASSWORD']
        if 'VERIFY' in config:
            self.verify_tls = config['VERIFY']
        else:
            self.verify_tls = True

    def get_device_info(self):
        ''' Method to get chassis info '''
        url = self.url + '/rpc/get-chassis-inventory'
        header = {'Accept': 'application/json',
                  'Content-Type': 'application/xml'}
        http = requests.Session()
        http.auth = (self.username, self.user_password)
        try:
            logger.debug("URL: %s", url)
            request = http.get(url, headers=header, verify=self.verify_tls)
        except RequestException as e:
            logger.error("Error connecting to Junos device. %s", e)
            return False
        if request.status_code == requests.codes.ok:
            json_data = request.json()
            chassis_inventory = json_data.get("chassis-inventory", [])
            for chassis_item in chassis_inventory:
                chassis_list = chassis_item.get("chassis", [])
                for chassis in chassis_list:
                    self.serial_number = chassis.get("serial-number", [{}])[0].get("data", "N/A")
                    logger.debug("Serial Number: %s", self.serial_number)
                    self.description = chassis.get("description", [{}])[0].get("data", "N/A")
                    logger.debug("Description: %s", self.description)
        else:
            logger.error('Error while requesting chassis info.'
                        ' Status code: %s Message: %s', request.status_code, request.text)
            return

    def get_interfaces(self):
        ''' Get all interface information '''
        url = self.url + '/rpc/get-interface-information'
        header = {'Accept': 'application/json',
                  'Content-Type': 'application/xml'}
        http = requests.Session()
        http.auth = (self.username, self.user_password)
        try:
            logger.debug("URL: %s", url)
            request = http.get(url, headers=header, verify=self.verify_tls)
        except RequestException as e:
            logger.error("Error getting Junos device interfaces. %s", e)
            return False
        if request.status_code == requests.codes.ok:
            json_data = request.json()
#            interface_information = json_data.get("interface-information", [])
            physical_interface = json_data.get("interface-information", [{}])[0].get("physical-interface", "N/A")
            for interface in physical_interface:
                name = interface.get("name", [{}])[0].get("data", "N/A")
                admin_status = interface.get("admin-status", [{}])[0].get("data", "N/A")
                oper_status = interface.get("oper-status", [{}])[0].get("data", "N/A")
                description = interface.get("description", [{}])[0].get("data", "N/A")
                statistics = interface.get("traffic-statistics", [])
                for traffic_statistics in statistics:
                    input_bps = traffic_statistics.get("input-bps", [{}])[0].get("data", "N/A")
                    input_pps = traffic_statistics.get("input-pps", [{}])[0].get("data", "N/A")
                    output_bps = traffic_statistics.get("output-bps", [{}])[0].get("data", "N/A")
                    output_pps = traffic_statistics.get("output-pps", [{}])[0].get("data", "N/A")
                alarms = interface.get("active-alarms", [])
                for alarm in alarms:
                    active_alarms = alarm.get("active-alarms", [])
                self.interfaces.append({"name": name, "description": description, "oper_status": oper_status, "input_bps": input_bps, "output_bps": output_bps, "input_pps": input_pps, "output_pps": output_pps, "active_alarms": active_alarms})
        else:
            logger.error('Error while requesting interface info.'
                        ' Status code: %s Message: %s', request.status_code, request.text)
            return

    def get_sensors(self):
        return self.interfaces


    def update(self):
        ''' Get new data from Junos API '''
        if self.skip_next:
            logger.debug("Skipping update due to setting change")
            self.skip_next = False
            return
        result = self.get_interfaces()
        return result