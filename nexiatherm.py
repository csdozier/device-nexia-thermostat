__author__ = 'scdozier'
__author__ = 'scdozier'
import sys
import os
from requests import session,exceptions
from collections import OrderedDict
import bs4 as BeautifulSoup
import logging
import logging.handlers
import traceback
import json
import asyncore, asynchat
import ConfigParser
import datetime
import os, socket, string, sys, httplib, urllib, urlparse, ssl
import StringIO, mimetools
import json
import hashlib
import time
import getopt
import requests
import time
from threading import Thread
import traceback
from threading import Thread
import base64

DEBUG = False
log = logging.getLogger('root')

def dict_merge(a, b):
    c = a.copy()
    c.update(b)
    return c

def start_logger(configfile):
    FORMAT = "%(asctime)-15s [%(filename)s:%(funcName)1s()] - %(levelname)s - %(message)s"
    logging.basicConfig(format=FORMAT)
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(config.LOGFILE,
                                           maxBytes=2000000,
                                           backupCount=2,
                                           )
    formatter = logging.Formatter(FORMAT)
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.info('Logging started..')

    #http debugging
    if DEBUG:
        try:
            import http.client as http_client
        except ImportError:
            # Python 2
            import httplib as http_client
        http_client.HTTPConnection.debuglevel = 1
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

def logger(message, level = 'info'):
    if 'info' in level:
        log.info(message)
    elif 'error' in level:
        log.error(message)
    elif 'debug' in level:
        log.debug(message)


class NexiaProxyServerConfig():
    def __init__(self, configfile):

        self._config = ConfigParser.ConfigParser()
        self._config.read(configfile)

        self.LOGFILE = self.read_config_var('main', 'logfile', '', 'str')
        self.LOGURLREQUESTS = self.read_config_var('main', 'logurlrequests', True, 'bool')
        self.PORT = self.read_config_var('main', 'port', 443, 'int')
        self.USETLS = self.read_config_var('main', 'use_tls', False, 'bool')
        self.CERTFILE = self.read_config_var('main', 'certfile', 'server.crt', 'str')
        self.KEYFILE = self.read_config_var('main', 'keyfile', 'server.key', 'str')
        self.NEXIAUSERNAME = self.read_config_var('nexia', 'username', '', 'str')
        self.NEXIAPASSWORD = self.read_config_var('nexia', 'password', '', 'str')
        self.NEXIAPOLLINTERVAL = self.read_config_var('nexia', 'poll_interval', '', 'int')
        self.CALLBACKURL_BASE = self.read_config_var('main', 'callbackurl_base', '', 'str')
        self.CALLBACKURL_APP_ID = self.read_config_var('main', 'callbackurl_app_id', '', 'str')
        self.CALLBACKURL_ACCESS_TOKEN = self.read_config_var('main', 'callbackurl_access_token', '', 'str')
        self.CALLBACKURL_NEXIA_DEVICE_ID = self.read_config_var('main', 'callbackurl_nexia_therm_device_id', '', 'str')


        global LOGTOFILE
        if self.LOGFILE == '':
            LOGTOFILE = False
        else:
            LOGTOFILE = True

        self.INPUTNAMES={}
        for i in (24,53,06,25,02,44,41,46,38,33,17,23,22,21,20,19):
            self.INPUTNAMES[i]=self.read_config_var('inputs', str(i), False, 'str', True)


    def defaulting(self, section, variable, default, quiet = False):
        if quiet == False:
            print('Config option '+ str(variable) + ' not set in ['+str(section)+'] defaulting to: \''+str(default)+'\'')

    def read_config_var(self, section, variable, default, type = 'str', quiet = False):
        try:
            if type == 'str':
                return self._config.get(section,variable)
            elif type == 'bool':
                return self._config.getboolean(section,variable)
            elif type == 'int':
                return int(self._config.get(section,variable))
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            self.defaulting(section, variable, default, quiet)
            return default
    def read_config_sec(self, section):
        try:
            return self._config._sections[section]
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            return {}


class NexiaThermostat(object):
    thermostatOperatingState ='' #anything? currentState "Cooling and is running"
    thermostatMode ='' #OFF/AUTO/HEAT/COOL
    thermostatFanMode ='' #on/off/auto/circuate
    humidity =''
    heatingSetpoint = ''
    coolingSetpoint =''
    thermostatSetpoint =''
    temperature = 0.0

    _NEXIA_LOGIN_URL = 'https://www.mynexia.com/login'
    _NEXIA_SESSION_URL = 'https://www.mynexia.com/session'
    _NEXIA_THERMOSTAT_STATUS_JSON_URL = 'https://www.mynexia.com/houses/<houseid>/xxl_thermostats'
    _NEXIA_ZONE_STATUS_URL = 'https://www.mynexia.com/houses/<houseid>/xxl_zones/<id>/zone_mode' #for change mode
    _NEXIA_SETPOINTS_URL = 'https://www.mynexia.com/houses/<houseid>/xxl_zones/<id>/setpoints' #for up/down temp
    _NEXIA_RETURNSCHEDULE_URL = 'https://www.mynexia.com/houses/<houseid>/xxl_zones/<id>/return_to_schedule'
    _NEXIA_MAIN_URL = 'https://www.mynexia.com'
    _NEXIA_SETFANMODE_URL = 'https://www.mynexia.com/houses/<houseid>/xxl_thermostats/<thermid>/fan_mode'
    _NEXIA_AWAY_URL =  'https://www.mynexia.com/houses/<houseid>/xxl_zones/<id>/preset'

    _headers = {
        'Accept': 'application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive',
        'Host': 'www.mynexia.com',
        'Referrer': 'https://www.mynexia.com/login',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16',
        'X-Requested-With': 'XMLHttpRequest'
    }

    _headers_when_sending = {
        'Accept': 'application/json',
        'Accept-Encoding': 'gzip,deflate,sdch',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive',
        'Host': 'www.mynexia.com',
        'Referrer': 'https://www.mynexia.com/login',
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16',
        'X-Requested-With': 'XMLHttpRequest'
    }

    def __init__(self,config):
        self.username = config.NEXIAUSERNAME
        self.password = config.NEXIAPASSWORD

        self._payload = {
        'authenticity_token': '',
        'login': self.username,
        'password': self.password,
        'utf': '%E2%9C%93'
         }

    def _update_urls(self,nexia_main_request_test):
        #get the houseid and set it in the global urls
        if 'window.Nexia.modes.houseId' in nexia_main_request_test:
            houseid = nexia_main_request_test.split('window.Nexia.modes.houseId = ')[1].split(';')[0]
            self._NEXIA_THERMOSTAT_STATUS_JSON_URL = self._NEXIA_THERMOSTAT_STATUS_JSON_URL.replace('<houseid>',houseid)
            self._NEXIA_ZONE_STATUS_URL = self._NEXIA_ZONE_STATUS_URL.replace('<houseid>',houseid)
            self._NEXIA_SETPOINTS_URL  =self._NEXIA_SETPOINTS_URL.replace('<houseid>',houseid)
            self._NEXIA_RETURNSCHEDULE_URL = self._NEXIA_RETURNSCHEDULE_URL.replace('<houseid>',houseid)
            self._NEXIA_SETFANMODE_URL = self._NEXIA_SETFANMODE_URL.replace('<houseid>',houseid)
            self._NEXIA_AWAY_URL = self._NEXIA_AWAY_URL.replace('<houseid>',houseid)

    def poll_thermostat_data(self):
        #Logs into mynexia.com and retrieves data on thermostat
        with session() as c:
            try:
                request = c.get(self._NEXIA_LOGIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies) #get authenticity token
                if 'csrf-token' in request.text:
                    token = request.text.split('name="csrf-param" />')[1].split('"')[1].split('"')[0]
                    self._headers['authenticity_token'] = token
                    self._headers['X-CSRF-Token'] = token
                logger('Logging into mynexia.com...')
                c.post(self._NEXIA_SESSION_URL, data=self._payload,verify=False,headers=self._headers,cookies=c.cookies,timeout=200)
                request = c.get(self._NEXIA_MAIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                self._update_urls(request.text)
                logger('Getting current thermostat data..')
                #retrieve json
                request = c.get(self._NEXIA_THERMOSTAT_STATUS_JSON_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                data = json.loads(request.text, object_pairs_hook=OrderedDict)
                self.thermdict = data
                #set variables
                self._NEXIA_ZONE_STATUS_URL = self._NEXIA_ZONE_STATUS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                self._NEXIA_SETPOINTS_URL  =self._NEXIA_SETPOINTS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                self.humidity = str(int(data[0]['current_relative_humidity']*100))
                self.temperature = str(data[0]['zones'][0]['temperature'])
                self.thermostatOperatingState= str(data[0]['system_status'])
                self.thermostatMode = str(data[0]['operating_mode'])
                self.thermostatFanMode = str(data[0]['fan_mode'])
                self.heatingSetpoint = str(data[0]['zones'][0]['heating_setpoint'])
                self.coolingSetpoint = str(data[0]['zones'][0]['cooling_setpoint'])
                logger('Humidity:'+self.humidity+' Temp:'+self.temperature+' Therm Op State:'+self.thermostatOperatingState)
                logger(' Therm Mode:'+self.thermostatMode+' Therm Fan Mode:'+self.thermostatFanMode+' Heat Set:'+self.heatingSetpoint
                                + ' Cool Set:'+self.coolingSetpoint)

            except Exception as ex:
                tb = traceback.format_exc()
                logger("Exception: "+str(ex.message)+tb)

    def set_mode(self,mode):
        #sets requested_zone_mode to OFF,HEAT,COOL, or AUTO
        with session() as c:
            try:
                request = c.get(self._NEXIA_LOGIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies) #get authenticity token
                if 'csrf-token' in request.text:
                    token = request.text.split('name="csrf-param" />')[1].split('"')[1].split('"')[0]
                    self._headers['authenticity_token'] = token
                    self._headers['X-CSRF-Token'] = token
                logger('Logging into mynexia.com...')
                c.post(self._NEXIA_SESSION_URL, data=self._payload,verify=False,headers=self._headers,cookies=c.cookies,timeout=200)
                request = c.get(self._NEXIA_MAIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                logger('Getting current thermostat data..')
                self._update_urls(request.text)
                request = c.get(self._NEXIA_THERMOSTAT_STATUS_JSON_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                data = json.loads(request.text, object_pairs_hook=OrderedDict)
                #set variables
                self._NEXIA_ZONE_STATUS_URL = self._NEXIA_ZONE_STATUS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                self._NEXIA_SETPOINTS_URL  =self._NEXIA_SETPOINTS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                thermdict = data[0]['zones'][0]
                #set mode based on requested_zone_mode
                if 'HEAT' in mode or 'AUTO' in mode or 'OFF' in mode or 'COOL' in mode:
                    thermdict['requested_zone_mode'] = mode
                    #todo puts json as payload
                    logger('Setting mode to :'+mode)
                    test= json.dumps(thermdict,separators=(',', ':'))
                    c.put(self._NEXIA_ZONE_STATUS_URL, data=test,verify=False,headers=self._headers_when_sending,cookies=c.cookies,timeout=200)
            except Exception as ex:
                tb = traceback.format_exc()
                logger("Exception: "+str(ex.message)+str(tb))



    def set_fan_mode(self,mode):
        #sets fane_mode to On,auto,circulate
        with session() as c:
            try:
                request = c.get(self._NEXIA_LOGIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies) #get authenticity token
                if 'csrf-token' in request.text:
                    token = request.text.split('name="csrf-param" />')[1].split('"')[1].split('"')[0]
                    self._headers['authenticity_token'] = token
                    self._headers['X-CSRF-Token'] = token
                logger('Logging into mynexia.com...')
                c.post(self._NEXIA_SESSION_URL, data=self._payload,verify=False,headers=self._headers,cookies=c.cookies,timeout=200)
                request = c.get(self._NEXIA_MAIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                logger('Getting current thermostat data..')
                self._update_urls(request.text)
                request = c.get(self._NEXIA_THERMOSTAT_STATUS_JSON_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                data = json.loads(request.text, object_pairs_hook=OrderedDict)
                thermdict = data[0]['zones'][0]
                #set mode based on requested_zone_mode
                if 'auto' in mode.lower() or 'circulate' in mode.lower() or 'on' in mode.lower():
                    thermdict['fan_mode'] = mode
                    #todo puts json as payload
                    logger('Setting fan mode to :'+mode)
                    test= json.dumps(thermdict,separators=(',', ':'))
                    c.put(self._NEXIA_SETFANMODE_URL.replace('<thermid>',str(thermdict['xxl_thermostat_id'])), data=test,verify=False,headers=self._headers_when_sending,cookies=c.cookies,timeout=200)
            except Exception as ex:
                tb = traceback.format_exc()
                logger("Exception: "+str(ex.message)+str(tb))

    def set_heating_setpoint(self,temp):
        with session() as c:
            try:
                request = c.get(self._NEXIA_LOGIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies) #get authenticity token
                if 'csrf-token' in request.text:
                    token = request.text.split('name="csrf-param" />')[1].split('"')[1].split('"')[0]
                    self._headers['authenticity_token'] = token
                    self._headers['X-CSRF-Token'] = token
                logger('Logging into mynexia.com...')
                c.post(self._NEXIA_SESSION_URL, data=self._payload,verify=False,headers=self._headers,cookies=c.cookies,timeout=200)
                request = c.get(self._NEXIA_MAIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                logger('Getting current thermostat data..')
                self._update_urls(request.text)
                request = c.get(self._NEXIA_THERMOSTAT_STATUS_JSON_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                data = json.loads(request.text, object_pairs_hook=OrderedDict)
                #set variables
                self._NEXIA_ZONE_STATUS_URL = self._NEXIA_ZONE_STATUS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                self._NEXIA_SETPOINTS_URL  =self._NEXIA_SETPOINTS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                thermdict = data[0]['zones'][0]
                #set heat setpoint
                thermdict['heating_integer'] = str(int(temp))
                thermdict['heating_setpoint'] = int(temp)
                logger('Setting heat setpoint to :'+temp)
                test= json.dumps(thermdict,separators=(',', ':'))
                c.put(self._NEXIA_SETPOINTS_URL, data=test,verify=False,headers=self._headers_when_sending,cookies=c.cookies,timeout=200)
            except Exception as ex:
                tb = traceback.format_exc()
                logger("Exception: "+str(ex.message)+str(tb))

    def set_cooling_setpoint(self,temp):
        with session() as c:
            try:
                request = c.get(self._NEXIA_LOGIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies) #get authenticity token
                if 'csrf-token' in request.text:
                    token = request.text.split('name="csrf-param" />')[1].split('"')[1].split('"')[0]
                    self._headers['authenticity_token'] = token
                    self._headers['X-CSRF-Token'] = token
                logger('Logging into mynexia.com...')
                c.post(self._NEXIA_SESSION_URL, data=self._payload,verify=False,headers=self._headers,cookies=c.cookies,timeout=200)
                request = c.get(self._NEXIA_MAIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                logger('Getting current thermostat data..')
                self._update_urls(request.text)
                request = c.get(self._NEXIA_THERMOSTAT_STATUS_JSON_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                data = json.loads(request.text, object_pairs_hook=OrderedDict)
                #set variables
                self._NEXIA_ZONE_STATUS_URL = self._NEXIA_ZONE_STATUS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                self._NEXIA_SETPOINTS_URL  =self._NEXIA_SETPOINTS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                thermdict = data[0]['zones'][0]
                #set heat setpoint
                thermdict['cooling_integer'] = str(int(temp))
                thermdict['cooling_setpoint'] = int(temp)
                logger('Setting cool setpoint to :'+temp)
                test= json.dumps(thermdict,separators=(',', ':'))
                c.put(self._NEXIA_SETPOINTS_URL, data=test,verify=False,headers=self._headers_when_sending,cookies=c.cookies,timeout=200)
            except Exception as ex:
                tb = traceback.format_exc()
                logger("Exception: "+str(ex.message)+str(tb))

    def set_away(self):
        with session() as c:
            try:
                request = c.get(self._NEXIA_LOGIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies) #get authenticity token
                if 'csrf-token' in request.text:
                    token = request.text.split('name="csrf-param" />')[1].split('"')[1].split('"')[0]
                    self._headers['authenticity_token'] = token
                    self._headers['X-CSRF-Token'] = token
                logger('Logging into mynexia.com...')
                c.post(self._NEXIA_SESSION_URL, data=self._payload,verify=False,headers=self._headers,cookies=c.cookies,timeout=200)
                request = c.get(self._NEXIA_MAIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                logger('Getting current thermostat data..')
                self._update_urls(request.text)
                request = c.get(self._NEXIA_THERMOSTAT_STATUS_JSON_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                data = json.loads(request.text, object_pairs_hook=OrderedDict)
                #set variables
                self._NEXIA_ZONE_STATUS_URL = self._NEXIA_ZONE_STATUS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                self._NEXIA_AWAY_URL  =self._NEXIA_AWAY_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                thermdict = data[0]['zones'][0]
                #set heat setpoint
                thermdict['schedule_status'] = 'OVRR'
                thermdict['preset_selected'] = 'away'
                logger('Setting away preset..')
                test= json.dumps(thermdict,separators=(',', ':'))
                c.put(self._NEXIA_AWAY_URL, data=test,verify=False,headers=self._headers_when_sending,cookies=c.cookies,timeout=200)
            except Exception as ex:
                tb = traceback.format_exc()
                logger("Exception: "+str(ex.message)+str(tb))


    def return_to_schedule(self):
        with session() as c:
            try:
                request = c.get(self._NEXIA_LOGIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies) #get authenticity token
                if 'csrf-token' in request.text:
                    token = request.text.split('name="csrf-param" />')[1].split('"')[1].split('"')[0]
                    self._headers['authenticity_token'] = token
                    self._headers['X-CSRF-Token'] = token
                logger('Logging into mynexia.com...')
                c.post(self._NEXIA_SESSION_URL, data=self._payload,verify=False,headers=self._headers,cookies=c.cookies,timeout=200)
                request = c.get(self._NEXIA_MAIN_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                logger('Getting current thermostat data..')
                self._update_urls(request.text)
                request = c.get(self._NEXIA_THERMOSTAT_STATUS_JSON_URL, timeout=200, verify=False,headers=self._headers,cookies=c.cookies)
                data = json.loads(request.text, object_pairs_hook=OrderedDict)
                #set variables
                self._NEXIA_ZONE_STATUS_URL = self._NEXIA_ZONE_STATUS_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                self._NEXIA_RETURNSCHEDULE_URL  =self._NEXIA_RETURNSCHEDULE_URL.replace('<id>',str(data[0]['zones'][0]['id']))
                thermdict = data[0]['zones'][0]
                #set return to schedule
                logger('Setting return to schedule..')
                thermdict['preset_selected'] = 'none'
                thermdict['schedule_status'] = 'RUN'
                test= json.dumps(thermdict,separators=(',', ':'))
                c.put(self._NEXIA_RETURNSCHEDULE_URL, data=test,verify=False,headers=self._headers_when_sending,cookies=c.cookies,timeout=200)
            except Exception as ex:
                tb = traceback.format_exc()
                logger("Exception: "+str(ex.message)+str(tb))


    def get_thermostat_data(self):
        return {
            'humidity' : self.humidity,
            'temperature' : self.temperature,
            'thermostatOperatingState': self.thermostatOperatingState,
            'thermostatMode' : self.thermostatMode,
            'thermostatFanMode' : self.thermostatFanMode,
            'heatingSetpoint' : self.heatingSetpoint,
            'coolingSetpoint' : self.coolingSetpoint,
        }

    def get_humidity(self):
        return self.humidity

    def get_temperature(self):
        return self.temperature

    def get_thermostat_operating_state(self):
        return self.thermostatOperatingState

    def get_thermostat_mode(self):
        return self.thermostatMode

    def get_thermostat_fan_mode(self):
        return self.thermostatFanMode

    def get_heating_setpoint(self):
        return self.heatingSetpoint

    def get_cooling_setpoint(self):
        return self.coolingSetpoint


class HTTPChannel(asynchat.async_chat):
    def __init__(self, server, sock, addr):
        asynchat.async_chat.__init__(self, sock)
        self.server = server
        self.set_terminator("\r\n\r\n")
        self.header = None
        self.data = ""
        self.shutdown = 0

    def collect_incoming_data(self, data):
        self.data = self.data + data
        if len(self.data) > 16384:
        # limit the header size to prevent attacks
            self.shutdown = 1

    def found_terminator(self):
        if not self.header:
            # parse http header
            fp = StringIO.StringIO(self.data)
            request = string.split(fp.readline(), None, 2)
            if len(request) != 3:
                # badly formed request; just shut down
                self.shutdown = 1
            else:
                # parse message header
                self.header = mimetools.Message(fp)
                self.set_terminator("\r\n")
                self.server.handle_request(
                    self, request[0], request[1], self.header
                    )
                self.close_when_done()
            self.data = ""
        else:
            pass # ignore body data, for now

    def pushstatus(self, status, explanation="OK"):
        self.push("HTTP/1.0 %d %s\r\n" % (status, explanation))

    def pushok(self, content):
        self.pushstatus(200, "OK")
        self.push('Content-type: application/json\r\n')
        self.push('Expires: Sat, 26 Jul 1997 05:00:00 GMT\r\n')
        self.push('Last-Modified: '+ datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")+' GMT\r\n')
        self.push('Cache-Control: no-store, no-cache, must-revalidate\r\n' )
        self.push('Cache-Control: post-check=0, pre-check=0\r\n')
        self.push('Pragma: no-cache\r\n' )
        self.push('\r\n')
        self.push(content)

    def pushfile(self, file):
        self.pushstatus(200, "OK")
        extension = os.path.splitext(file)[1]
        if extension == ".html":
            self.push("Content-type: text/html\r\n")
        elif extension == ".js":
            self.push("Content-type: text/javascript\r\n")
        elif extension == ".png":
            self.push("Content-type: image/png\r\n")
        elif extension == ".css":
            self.push("Content-type: text/css\r\n")
        self.push("\r\n")
        self.push_with_producer(push_FileProducer(sys.path[0] + os.sep + 'ext' + os.sep + file))

class push_FileProducer:
    # a producer which reads data from a file object

    def __init__(self, file):
        self.file = open(file, "rb")

    def more(self):
        if self.file:
            data = self.file.read(2048)
            if data:
                return data
            self.file = None
        return ""

class NexiaStatusPoller(Thread):

    def __init__(self, nexia_thermostat,poll_interval=300):
        super(NexiaStatusPoller, self).__init__()
        self.nexia_thermostat = nexia_thermostat
        self.poll_interval = poll_interval
        self.daemon = True

    def run(self):
        st_URL_prefix = config.CALLBACKURL_BASE + "/" + config.CALLBACKURL_APP_ID + "/nexiatherm/" + str(config.CALLBACKURL_NEXIA_DEVICE_ID) + "/"
        st_URL_suffix = "?access_token=" + config.CALLBACKURL_ACCESS_TOKEN
        data = {
            'humidity' : '0',
            'temperature' : '0',
            'thermostatOperatingState': 'n/a',
            'thermostatMode' : 'n/a',
            'thermostatFanMode' : 'n/a',
            'heatingSetpoint' : '0',
            'coolingSetpoint' : '0',
        }
        while 1:
            try:
                #poll mynexia.com for new data
                self.nexia_thermostat.poll_thermostat_data()
                #check if values changed, if so send data to ST
                new_data = self.nexia_thermostat.get_thermostat_data()
                for item in new_data.keys():
                    if data[item] != new_data[item]:
                        logger('TX > HTTP GET: '+st_URL_prefix+item+'/'+urllib.quote_plus(new_data[item])+st_URL_suffix)
                        my_requests_thread = RequestsThread(st_URL_prefix+item+'/'+urllib.quote_plus(new_data[item]),access_token=config.CALLBACKURL_ACCESS_TOKEN)
                        my_requests_thread.start()
                        data[item] = new_data[item]
                #sleep
                logger('Polling sleeping for '+str(self.poll_interval)+' seconds..')
                time.sleep(self.poll_interval)
            except Exception as ex:
                tb = traceback.format_exc()
                logger('Exception! '+ str(ex.message)+str(tb))



class NexiaProxyServer(asyncore.dispatcher):

    def __init__(self, config):
        # Call parent class's __init__ method
        asyncore.dispatcher.__init__(self)

        # Create Nexia Receiver Control object
        self._nexia_thermostat = NexiaThermostat(config)

        #Store config
        self._config = config

        # Create socket and listen on it
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.bind(("", config.PORT))
        self.listen(5)
        logger('Listening for HTTP(S) connections on port: '+str(config.PORT))

        #Start Thermostat Poller
        _nexiapoller = NexiaStatusPoller(self._nexia_thermostat,config.NEXIAPOLLINTERVAL)
        _nexiapoller.start()


    def handle_accept(self):
        # Accept the connection
        conn, addr = self.accept()
        if (config.LOGURLREQUESTS):
            logger('Incoming web connection from %s' % repr(addr))

        try:
            if config.USETLS:
                HTTPChannel(self, ssl.wrap_socket(conn, server_side=True, certfile=config.CERTFILE, keyfile=config.KEYFILE, ssl_version=ssl.PROTOCOL_TLSv1), addr)
            else:
                HTTPChannel(self, conn, addr) #use non ssl
        except ssl.SSLError:
            return

    def handle_request(self, channel, method, request, header):
        st_URL_prefix = config.CALLBACKURL_BASE + "/" + config.CALLBACKURL_APP_ID + "/nexiatherm/" + str(config.CALLBACKURL_NEXIA_DEVICE_ID) + "/"
        st_URL_suffix = "?access_token=" + config.CALLBACKURL_ACCESS_TOKEN
        if (config.LOGURLREQUESTS):
            logger('Web request: '+str(method)+' '+str(request))

        query = urlparse.urlparse(request)
        query_array = urlparse.parse_qs(query.query, True)
        path = query.path
        try:
            if '&apiserverurl' in query.path:
                path,base64url = query.path.split('&apiserverurl=')
                url = urllib.unquote(base64url).decode('utf8')
                if url not in config.CALLBACKURL_BASE:
                    url = url.replace('http:','https:')
                    logger('Setting API Base URL To: '+url)
                    config.CALLBACKURL_BASE = url
            logger(path)
            if path == '/':
                channel.pushstatus(404, "Not found")
            elif '/nexiatherm/refresh' in path:  #power on/off main zone
                if path.split('/')[-1] == 'on':
                    channel.pushok(json.dumps({'response' : 'Refreshing thermostat data...'}))
                   # self._VSXControl.send_command('PO')
            #'humidity' : '0',
            #'temperature' : '0',
            #'thermostatOperatingState': 'n/a',
            #'thermostatMode' : 'n/a',
            #'thermostatFanMode' : 'n/a',
            #'heatingSetpoint' : '0',
            #'coolingSetpoint' : '0',
            elif '/nexiatherm/refresh' in path:  #power on/off main zone
                if path.split('/')[-1] == 'on':
                    channel.pushok(json.dumps({'response' : 'Refreshing thermostat data...'}))
                    new_data = self._nexia_thermostat.get_thermostat_data()
                    for item in new_data.keys():
                        logger('TX > HTTP GET: '+st_URL_prefix+item+'/'+urllib.quote_plus(new_data[item])+st_URL_suffix)
                        my_requests_thread = RequestsThread(st_URL_prefix+item+'/'+urllib.quote_plus(new_data[item]),access_token=config.CALLBACKURL_ACCESS_TOKEN)
                        my_requests_thread.start()
            elif '/nexiatherm/fanmode/set' in path:  #power on/off main zone
                mode = path.split('/')[-1]
                channel.pushok(json.dumps({'response' : 'Setting fan mode '+mode+'...'}))
                self._nexia_thermostat.set_fan_mode(mode)
            elif '/nexiatherm/mode/set' in path:  #power on/off main zone
                mode = path.split('/')[-1]
                channel.pushok(json.dumps({'response' : 'Setting mode '+mode+'...'}))
                self._nexia_thermostat.set_mode(mode)
            elif '/nexiatherm/heatpoint/set' in path:  #power on/off main zone
                temp = path.split('/')[-1]
                channel.pushok(json.dumps({'response' : 'Setting temperature heatpoint to '+temp+'...'}))
                self._nexia_thermostat.set_heating_setpoint(temp)
            elif '/nexiatherm/coolpoint/set' in path:  #power on/off main zone
                temp = path.split('/')[-1]
                channel.pushok(json.dumps({'response' : 'Setting temperature coolpoint to '+temp+'...'}))
                self._nexia_thermostat.set_cooling_setpoint(temp)
            elif '/nexiatherm/setaway' in path:  #set away
                channel.pushok(json.dumps({'response' : 'Setting away '+'...'}))
                self._nexia_thermostat.set_away()
            elif '/nexiatherm/runschedule' in path:  #set away
                channel.pushok(json.dumps({'response' : 'Returning to schedule '+'...'}))
                self._nexia_thermostat.return_to_schedule()
            else:
                channel.pushstatus(404, "Not found")
                channel.push("Content-type: text/html\r\n")
                channel.push("\r\n")
        except Exception as ex:
            tb = traceback.format_exc()
            logger('Exception! '+ str(ex.message)+str(tb))

class RequestsThread(Thread):
    def __init__(self,url,method='get',access_token=''):
        super(RequestsThread, self).__init__()
        self.daemon = True
        """Initialize"""
        self.url = url
        self.method = method
        self.access_token = access_token
    def run(self):
        headers = {'Authorization': 'Bearer {}'.format(self.access_token)}
        try:
            if 'get' in self.method:
                requests.get(self.url,timeout=20,headers=headers)
        except Exception as ex:
            tb = traceback.format_exc()
            logger('Exception! '+ str(ex.message)+str(tb)+'url:'+self.url)


def usage():
    print 'Usage: '+sys.argv[0]+' -c <configfile>'

def main(argv):
    try:
      opts, args = getopt.getopt(argv, "hc:", ["help", "config="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c", "--config"):
            global conffile
            conffile = arg



if __name__ == '__main__':
    conffile='nexiaproxysrvr.cfg'
    args = sys.argv[1:]
    #nexia_therm = NexiaThermostat()
    #drsstatus = nexia_therm.get_thermostat_data()
    #nexia_therm.set_mode('AUTO')
    main(sys.argv[1:])
    print('Using configuration file %s' % conffile)
    config = NexiaProxyServerConfig(conffile)
    start_logger(config.LOGFILE)
    logger('Writing logfile to %s' % config.LOGFILE)
    logger('Nexia Thermostat Proxy Server Starting')


    server = NexiaProxyServer(config)

    try:
        while True:
            asyncore.loop(timeout=2, count=1)
            # insert scheduling code here.
    except KeyboardInterrupt:
        print "Crtl+C pressed. Shutting down."
        logger('Shutting down from Ctrl+C')
        server.shutdown(socket.SHUT_RDWR)
        server.close()
        sys.exit()









