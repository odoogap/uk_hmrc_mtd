# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import uuid
import socket

from odoo import models, fields, api, _
from requests import get
from datetime import datetime
from dateutil.tz import tzlocal
from odoo.http import request


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
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

    def create_fraud_prevention_headers(self):
        public_ip = get('https://api.ipify.org').text
        public_vendor_ip = socket.gethostbyname('odoomtd.co.uk')
        params = self.env['ir.config_parameter'].sudo()
        gov_device_id = params.get_param('mtd.gov_device_id', default=False)
        date_string = str(datetime.now(tzlocal()))
        user = self.env['res.users'].sudo().browse(self.env.uid)
        timestamp = user.login_date.replace(" ", "T").replace(":", "%3A") + "Z"
        unique_reference = user.company_id.id
        public_ip_timestamp = datetime.utcnow().isoformat('T')[:-3] + 'Z'
        print public_ip_timestamp
        module_version = self.env['ir.module.module'].search([('name', '=', 'hmrc_mtd_client')]).installed_version
        licence_ids = self.env['ir.module.module'].search([('name', '=', 'hmrc_mtd_client')]).license

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
            'Gov-Client-Public-IP-Timestamp': public_ip_timestamp,
            'Gov-Client-Public-IP': public_ip,
            'Gov-Client-Public-Port': request.httprequest.environ.get('SERVER_PORT'),
            'Gov-Client-Device-ID': gov_device_id,
            'Gov-Client-User-IDs': 'My_Webapp_Software=' + str(self.env.user.id),
            'Gov-Client-Timezone': utc_time,
            'Gov-Client-Local-IPs-Timestamp': datetime.utcnow().isoformat('T')[:-3] + 'Z',
            'Gov-Client-Local-IPs': self.get_local_ip(),
            'Gov-Client-Screens': record.screens + "&scaling-factor=1.7777777777777777&colour-depth=24" if record else "width=1920&height=1080&scaling-factor=1.7777777777777777&colour-depth=24",
            'Gov-Client-Window-Size': record.window_size if record else "width=1920&height=1080",
            'Gov-Client-Browser-Plugins': record.browser_plugin if record else 'Native%20Client',
            'Gov-Client-Browser-JS-User-Agent': record.js_user_agent if record else "",
            'Gov-Client-Browser-Do-Not-Track': "false",
            'Gov-Client-Multi-Factor': "type=OTHER&timestamp=" + timestamp + "&unique-reference=" + str(hash(unique_reference)),
            'Gov-Vendor-Version': "hmrc_mtd_client" + "=" + str(module_version) + "&hmrc_mtd_server" + "=" + "0.1",
            'Gov-Vendor-License-IDs': "hmrc_mtd_server" + "=" + str(hash(licence_ids)),
            'Gov-Vendor-Public-IP': public_vendor_ip,
            'Gov-Vendor-Forwarded': "by=" + public_vendor_ip + "&for=" + public_ip,
            'Gov-Vendor-Product-Name': 'OdooGAP'
        }
