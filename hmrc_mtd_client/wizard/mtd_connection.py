# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
import odoorpc
from odoo.exceptions import UserError, RedirectWarning
import os
import ssl

class MtdConnection(models.TransientModel):
    _name = 'mtd.connection'

    def open_connection_odoogap(self):
        params = self.env['ir.config_parameter'].sudo()
        login = params.get_param('mtd.login', default=False)
        password = params.get_param('mtd.password', default=False)
        server = params.get_param('mtd.server', default=False)
        db = params.get_param('mtd.db', default=False)
        port = params.get_param('mtd.port', default=False)
        odoo_instance = odoorpc.ODOO(server, protocol='jsonrpc+ssl', port=int(port))
        odoo_instance.login(db, login, password)
        return odoo_instance

    @api.multi
    def get_authorization(self):
        conn = self.open_connection_odoogap()
        response = conn.execute('mtd.operations', 'authorize',
                                self.env['ir.config_parameter'].sudo().get_param('mtd.sandbox', default=False))
        if response.get('status') == 200:
            self.env['ir.config_parameter'].sudo().set_param('mtd.hmrc.url', response.get('mtd_url'))
            client_action = {'type': 'ir.actions.act_url', 'name': "HMRC authentication", 'target': 'new',
                             'url': response.get('message')}
            return client_action
        raise UserError(
            'An error has occurred : \n status: %s \n message: %s ' % (
                str(response.get('status')), response.get('message')))

    def refresh_token(self):
        conn = self.open_connection_odoogap()
        response = conn.execute('mtd.operations', 'refresh_token',
                                self.env['ir.config_parameter'].sudo().get_param('mtd.sandbox', default=False))
        if response.get('status') == 200:
            set_param = self.env['ir.config_parameter'].sudo().set_param
            set_param('mtd.token', response.get('message').get('token'))
            set_param('mtd.token_expire_date', response.get('message').get('exp_date'))
            return response.get('message').get('token')
        else:
            raise UserError(
                'An error has occurred : \n status: %s\n message: %s' % (
                    str(response.get('status')), response.get('message')))
