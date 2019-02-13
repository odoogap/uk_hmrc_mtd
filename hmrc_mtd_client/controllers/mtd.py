# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import http
from odoo.http import request
import webbrowser


class Mtd(http.Controller):

    @http.route('/mtd/<string:token>/<string:ex_date>', auth='user')
    def redirect(self, **kw):
        web_url = request.env['ir.config_parameter'].get_param('web.base.url')
        if kw.get('token') != 'Invalid':
            request.env['ir.config_parameter'].sudo().set_param('mtd.token', kw.get('token'))
            request.env['ir.config_parameter'].sudo().set_param('mtd.token_expire_date', float(kw.get('ex_date')))
            webbrowser.open_new(web_url + '/mtd/message/success')
        else:
            webbrowser.open_new(web_url + '/mtd/message/failure')

    @http.route('/mtd/message/<string:message>', auth='user')
    def redirect_message(self, **kw):
        if kw.get('message') == 'success':
            return 'Success! you can close the HMRC Page'
        else:
            return 'Failed! Something went wrong'
