import logging
import cgi
import urllib,urllib2
import datetime,time
from random import random
import json

from pylons import request, response, session, tmpl_context as c, url
from pylons.controllers.util import abort, redirect

from railstat.lib.base import BaseController, render

log = logging.getLogger(__name__)

class TrainStatusController(BaseController):

    def get_train_status(self):
        '''
            Input:
                1. train number
                2. train departure date(optional)
            Output:
                Last location of the train, time at which arrived at the last location, expected time for next location.
        '''
        res_msg = ''
        if request.params.has_key('txtweb-message'):
            txtweb_message = cgi.escape(request.params.get('txtweb-message'))
            if txtweb_message.__contains__(" "):
                train_number,train_start_date = txtweb_message.split()
            else:
                train_number = txtweb_message
                gmt_datetime = datetime.datetime.fromtimestamp(time.mktime(time.gmtime()))
                ist_datetime = gmt_datetime + datetime.timedelta(hours=5,minutes=30)
                ist_date = ist_datetime.date().isoformat()
                train_start_date = ist_date
            user_train_date = train_start_date
        else:
            help_msg = '<html><head><meta name="txtweb-appkey" content="app-id" /></head><body>Get latest update on your train running status. <br /> To use, SMS @railstat &lt;train number&gt; &lt;train departure date in the format yyyy-mm-dd&gt; to 92665 92665 <br />Eg: @railstat 12631 2012-06-25</body></html>'
            return help_msg
        random_number1 = random().__str__()[2:]
        random_number2 = random().__str__()[2:]
        main_page = urllib2.urlopen('http://trainenquiry.com')
        cookie_val = main_page.headers.get('Set-Cookie')
        json_train_schedule = self._get_train_schedule(train_number,train_start_date,cookie_val)
        train_station_info = {}
        all_station_codes = ''
        for each_schedule in json_train_schedule:
            if each_schedule['station_code'].strip() and each_schedule['stop']:
                train_station_info[each_schedule['station_code']] = each_schedule
            all_station_codes = '%s,%s'%(all_station_codes,each_schedule['station_code'])
        all_station_codes = all_station_codes[1:]
        json_content = self._get_train_location_info(train_number,train_start_date,all_station_codes,cookie_val) 
        if json_content.has_key('keys'):
            json_key = json_content['keys']
            train_start_date = json_key[0].replace('%s_'%train_number,'')
        if not json_content['%s_%s'%(train_number,train_start_date.replace('-','_'))]['running_info'].has_key('last_stn'):
            if json_train_schedule:
                for each_tr_stn in json_train_schedule:
                    if str(each_tr_stn['sta']) == 'None':
                        dept_time = each_tr_stn['std']
                        dept_name = each_tr_stn['station_name']
                        ft = datetime.datetime.strptime(dept_time,'%Y-%m-%dT%H:%M:%S+05:30')
                        readable_time =  '%s:%s' % (ft.hour, ft.minute)
                        readable_date =  '%s-%s-%s' % (ft.day, ft.month, ft.year)
                        tmp_msg = '<html><head><meta name="txtweb-appkey" content="app-id" /></head><body>Train(%s) is scheduled to start from %s at %s (%s)<br />Thanks to Railyatri.in</body></html>'%(train_number, dept_name, readable_time, readable_date)
                        res_msg = '%s%s'%(res_msg,tmp_msg)
                        break
            else:
                tmp_msg = '<html><head><meta name="txtweb-appkey" content="app-id" /></head><body>Sorry, No information is available for this train. <br /> Please try again later! <br />Thanks to Railyatri.in</body></html>'
                res_msg = '%s%s'%(res_msg,tmp_msg)
            return res_msg
        last_location = json_content['%s_%s'%(train_number,train_start_date.replace('-','_'))]['running_info']['last_stn']['station_name']
        last_location_code = json_content['%s_%s'%(train_number,train_start_date.replace('-','_'))]['running_info']['last_stn']['station_code']
        last_status = json_content['%s_%s'%(train_number,train_start_date.replace('-','_'))]['running_info']['last_stn']['status']
        last_time = json_content['%s_%s'%(train_number,train_start_date.replace('-','_'))]['running_info']['last_stn']['time']
        current_last_station = last_location_code
           
        next_station_code = ''
        if not json_content['%s_%s'%(train_number,train_start_date.replace('-','_'))].has_key('station_updates'):
            tmp_msg = '<html><head><meta name="txtweb-appkey" content="app-id" /></head><body>Sorry, No information is available for this train. <br /> Please try again later! <br />Thanks to Railyatri.in</body></html>'
            res_msg = '%s%s'%(res_msg,tmp_msg)
            return res_msg
        station_updates = json_content['%s_%s'%(train_number,train_start_date.replace('-','_'))]['station_updates']
        delay_mins = ''
        station_next_to_current = False
        for each_station_schedule in json_train_schedule:
            if each_station_schedule['station_code'] == last_location_code:
                station_next_to_current = True
                if last_status.startswith('arrived'):
                    last_location_sta = each_station_schedule['sta']
                else:
                    last_location_sta = each_station_schedule['std']
                ft = datetime.datetime.strptime(last_time,'%Y-%m-%dT%H:%M:%S+05:30')
                ft2 = datetime.datetime.strptime(last_location_sta,'%Y-%m-%dT%H:%M:%S+05:30')
                if ft2 > ft:
                    delay_mins = -((ft2 - ft).seconds/60)
                else:
                    delay_mins = (ft - ft2).seconds/60
                continue
            if not each_station_schedule['stop']:
                continue
            if station_next_to_current:
                if each_station_schedule['std'] == 'None':
                    next_station_code = 'ENDOFTRIP'
                else:
                    next_station_code = each_station_schedule['station_code']
                break
            if not last_location.strip() and last_location_code.strip():
                if each_station_schedule['station_code'] == last_location_code:
                    last_location = each_station_schedule['station_name']
        if not last_location.strip() and last_location_code.strip():
            for each_station_schedule in json_train_schedule:
                if each_station_schedule['station_code'] == last_location_code:
                    last_location = each_station_schedule['station_name']
                    break
        train_status = json_content['%s_%s'%(train_number,train_start_date.replace('-','_'))]['status']
        if next_station_code != 'ENDOFTRIP' and delay_mins == '':
            delay_mins = json_content['%s_%s'%(train_number,train_start_date.replace('-','_'))]['delay_mins']
            delay_mins = int(delay_mins)
            
        ft = datetime.datetime.strptime(last_time,'%Y-%m-%dT%H:%M:%S+05:30')
        readable_time =  '%s:%s' % (ft.hour, ft.minute)
        readable_date =  '%s-%s-%s' % (ft.day, ft.month, ft.year)
        msg = '<br /><br />Last Station: %s<br />Status: %s at %s on %s<br />Delay by: %s mins' % (last_location, last_status, readable_time, readable_date, delay_mins)
        if next_station_code and next_station_code != 'ENDOFTRIP':
            next_station_name = train_station_info[next_station_code]['station_name']
            ns_sta = train_station_info[next_station_code]['sta']
            ns_sta = datetime.datetime.strptime(ns_sta,'%Y-%m-%dT%H:%M:%S+05:30')
            ns_eta = ns_sta + datetime.timedelta(minutes=delay_mins)
            sta_time =  '%s:%s' % (ns_sta.hour, ns_sta.minute)
            sta_date =  '%s-%s-%s' % (ns_sta.day, ns_sta.month, ns_sta.year)
            eta_time =  '%s:%s' % (ns_eta.hour, ns_eta.minute)
            eta_date =  '%s-%s-%s' % (ns_eta.day, ns_eta.month, ns_eta.year)
            msg = msg+"<br /><br />Next Station update:<br /><br />Station Name: %s<br />Scheduled: %s(%s)<br />Expected: %s(%s)" % (next_station_name, sta_time, sta_date, eta_time, eta_date)
        tmp_msg = '<html><head><meta name="txtweb-appkey" content="app-id" /></head><body>Train running status update - %s : %s' % (train_number, user_train_date)
        tmp_msg = "%s%s"%(tmp_msg,msg+"<br />Thanks to Railyatri.in</body></html>")
        res_msg = '%s%s'%(res_msg,tmp_msg)
        return res_msg

    def _get_train_schedule(self,train_number,train_start_data,cookie_val):
        '''
            Fetches Train Schedule by using train number and train departure date
        '''
        train_schedule_url = 'http://www.trainenquiry.com/RailYatri.ashx'
        payload_data = {}
        payload_data['RequestType'] = 'Schedule'
        payload_data['date_variable'] = train_start_date
        payload_data['train_number_variable']  = train_number
        payload_data = urllib.urlencode(payload_data)
        sc_url_req = urllib2.Request(train_schedule_url)
        sc_url_req.add_header('Cookie',cookie_val) 
        sc_url_req.add_header('Referer','http://trainenquiry.com/CurrentRunningTrain.aspx') 
        s = urllib2.urlopen(sc_url_req,payload_data)
        train_schedule = s.read()
        json_train_schedule = json.loads(train_schedule.replace('jQuery%s('%random_number1, '').replace(')',''))
        return json_train_schedule

    def _get_train_location_info(self,train_number,train_start_data,all_station_codes,cookie_val):
        '''
            Fetches train location information which includes scheduled and actual departure,arrival times for each station
        '''
        train_schedule_url = 'http://www.trainenquiry.com/RailYatri.ashx'
        payload_data = {}
        payload_data['RequestType'] = 'Location'
        payload_data['codes'] = all_station_codes
        payload_data['s'] = train_start_date
        payload_data['t']  = train_number
        payload_data = urllib.urlencode(payload_data)
        sc_url_req = urllib2.Request(train_schedule_url)
        sc_url_req.add_header('Cookie',cookie_val) 
        sc_url_req.add_header('Referer','http://trainenquiry.com/CurrentRunningTrain.aspx') 
        s = urllib2.urlopen(sc_url_req,payload_data)
        status_content = s.read()
        json_content = json.loads(status_content.replace('jQuery%s('%random_number1, '').replace(')',''))
        return json_content
