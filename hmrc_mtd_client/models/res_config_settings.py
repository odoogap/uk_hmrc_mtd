# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
import os
import ssl

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    login = fields.Char('Name', help='Account name of mtd')
    password = fields.Char('Password', help='Account password of mtd')
    server = fields.Char('Server')
    db = fields.Char('Database')
    port = fields.Char('Port')
    token = fields.Char('token')
    period = fields.Selection(string='submission period',
                              selection=[('Q', 'Quarterly'), ('M', 'Monthly'), ('A', 'Annual')])
    is_sandbox = fields.Boolean('Enable sandbox', help='Enable sandbox environment on HMRC API', default=False)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        login = params.get_param('mtd.login', default=False)
        password = params.get_param('mtd.password', default=False)
        token = params.get_param('mtd.token', default=False)
        period = params.get_param('mtd.period', default=False)
        is_sandbox = params.get_param('mtd.sandbox', default=False)
        res.update(login=login, password=password, token=token, period=period, is_sandbox=is_sandbox)
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('mtd.login', self.login)
        set_param('mtd.password', self.password)
        set_param('mtd.period', self.period)
        set_param('mtd.sandbox', self.is_sandbox)

    @api.multi
    def get_authorization(self):
        return self.env['mtd.connection'].get_authorization()
