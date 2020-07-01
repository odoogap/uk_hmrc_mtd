# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from requests import get
import uuid
from datetime import datetime, timezone
from odoo.http import request
import socket
import time


class MtdFraudPrevention(models.TransientModel):
    _name = 'mtd.fraud.prevention'

    user_id = fields.Integer('User id')
    screens = fields.Char('Screens')
    window_size = fields.Char('Window size')
    js_user_agent = fields.Char('Js user agent')
    browser_plugin = fields.Char('Browser Plugins')

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
                'js_user_agent': data.get('js_user_agent', False),
                'browser_plugin': data.get('browser_plugin', False)
            })
        else:
            record.write({
                'user_id': self.env.user.id,
                'screens': data.get('screens', False),
                'window_size': data.get('window_size', False),
                'js_user_agent': data.get('js_user_agent', False),
                'browser_plugin': data.get('browser_plugin', False)
            })

    def get_local_ip(self):
        return ([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2]
                              if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)),
                                                                    s.getsockname()[0], s.close()) for s in
                                                                   [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][
                                                                      0][1]]) if l][0][0])

    def create_fraud_prevention_headers(self):
        public_ip = get('https://api.ipify.org').text
        public_vendor_ip = socket.gethostbyname('odoomtd.co.uk')
        params = self.env['ir.config_parameter'].sudo()
        gov_device_id = params.get_param('mtd.gov_device_id', default=False)
        date_string = str(datetime.now(timezone.utc).astimezone().isoformat())
        user = self.env['res.users'].sudo().browse(self.env.uid)
        timestamp = user.login_date.replace(" ", "T").replace(":", "%3A") + "Z"
        unique_reference = user.company_id.id

        params = self.env['ir.config_parameter'].sudo()
        api_token = params.get_param('mtd.token', default=False)
        token_expire_date = params.get_param('mtd.token_expire_date')

        if api_token:
            if float(token_expire_date) - time.time() < 0:
                self.env['mtd.connection'].refresh_token()

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
            'Gov-Client-Public-Port': request.httprequest.environ.get('SERVER_PORT'),
            'Gov-Client-Device-ID': gov_device_id,
            'Gov-Client-User-IDs': "web=" + str(self.env.user.id) + "&my-vendor-online-account=" + "null",
            'Gov-Client-Timezone': utc_time,
            'Gov-Client-Local-IPs': self.get_local_ip(),
            'Gov-Client-Screens': record.screens if record else "",
            'Gov-Client-Window-Size': record.window_size if record else "",
            'Gov-Client-Browser-Plugins': record.browser_plugin,
            'Gov-Client-Browser-JS-User-Agent': record.js_user_agent if record else "",
            'Gov-Client-Browser-Do-Not-Track': "false",
            'Gov-Client-Multi-Factor': "type=OTHER&timestamp=" + timestamp + "&unique-reference=" + str(
                hash(unique_reference)),
            'Gov-Vendor-Version': "hmrc_mtd_client" + "=" + "1.1.6" + "&hmrc_mtd_server" + "=" + "0.1",
            'Gov-Vendor-License-IDs': "hmrc_mtd_server" + "=" + str(hash(0.1)),
            'Gov-Vendor-Public-IP': public_vendor_ip,
            'Gov-Vendor-Forwarded': "by=" + public_vendor_ip + "&for=" + public_ip
        }
