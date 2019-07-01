# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from requests import get
import uuid
from datetime import datetime
from dateutil.tz import tzlocal
from odoo.http import request
import socket

class MtdFraudPrevention(models.TransientModel):
    _name = 'mtd.fraud.prevention'

    user_id = fields.Integer('User id')
    screens = fields.Char('Screens')
    window_size = fields.Char('Window size')
    js_user_agent = fields.Char('Js user agent')

    def generate_device_id(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        gov_client_device_id = str(uuid.uuid4())
        set_param('mtd.gov_device_id', gov_client_device_id)

        return gov_client_device_id

    @api.model
    def set_java_script_headers(self, data):
        record = self.search([('user_id', '=', self.env.user.id)], limit=1)
        if not record:
            self.create({
                'user_id': self.env.user.id,
                'screens': data.get('screens', False),
                'window_size': data.get('window_size', False),
                'js_user_agent': data.get('js_user_agent', False)
            })
        else:
            record.write({
                'user_id': self.env.user.id,
                'screens': data.get('screens', False),
                'window_size': data.get('window_size', False),
                'js_user_agent': data.get('js_user_agent', False)
            })

    def create_fraud_prevention_headers(self):
        public_ip = get('https://api.ipify.org').text
        public_vendor_ip = socket.gethostbyname('odoomtd.co.uk')
        params = self.env['ir.config_parameter'].sudo()
        gov_device_id = params.get_param('mtd.gov_device_id', default=False)
        utc_time = ""
        data = None
        date_string = str(datetime.now(tzlocal()))

        if not gov_device_id:
            gov_device_id = self.generate_device_id()

        if '+' in date_string:
            data = date_string.rsplit('+', 1)
            utc_time = "UTC+%s" % str(data[1]) 
        else:
            data = date_string.rsplit('-', 1)
            utc_time = "UTC-%s" % str(data[1])
        record = self.search([('user_id', '=', self.env.user.id)], limit=1)

        return {
            'Gov-Client-Connection-Method': 'WEB_APP_VIA_SERVER',
            'Gov-Client-Public-IP': public_ip,
            'Gov-Client-Public-Port':request.httprequest.environ.get('SERVER_PORT'),
            'Gov-Client-Device-ID': gov_device_id,
            'Gov-Client-Timezone': utc_time,
            'Gov-Client-Screens': record.screens if record else "",
            'Gov-Client-Window-Size': record.window_size if record else "",
            'Gov-Client-User-Agent': request.httprequest.environ.get('HTTP_USER_AGENT', '').lower(),
            'Gov-Client-Browser-JS-User-Agent': record.js_user_agent if record else "",
            'Gov-Vendor-Version': '1.1.5',
            'Gov-Vendor-Public-IP': public_vendor_ip
        }
