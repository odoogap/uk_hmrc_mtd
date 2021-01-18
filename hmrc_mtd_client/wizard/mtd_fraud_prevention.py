# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import uuid
import odoogap_mtd as mtd

from odoo import models, fields, api, _
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

    def create_fraud_prevention_headers(self):
        params = self.env['ir.config_parameter'].sudo()
        gov_device_id = params.get_param('mtd.gov_device_id', default=False)
        user = self.env['res.users'].sudo().browse(self.env.uid)
        login_date_format = user.login_date
        unique_reference = user.company_id.id
        module_version = self.env['ir.module.module'].search([('name', '=', 'hmrc_mtd_client')]).installed_version
        licence_ids = self.env['ir.module.module'].search([('name', '=', 'hmrc_mtd_client')]).license

        if not gov_device_id:
            gov_device_id = self.generate_device_id()

        record = self.search([('user_id', '=', self.env.user.id)], limit=1)

        return mtd.mtd_headers.create_headers_dic(request.httprequest.environ.get('SERVER_PORT'), gov_device_id,
                                                  user.id,
                                                  record.screens, record.window_size, record.browser_plugin,
                                                  record.js_user_agent, login_date_format, unique_reference,
                                                  module_version,
                                                  licence_ids)
