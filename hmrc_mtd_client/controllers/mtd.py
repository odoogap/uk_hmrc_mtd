# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import http
from odoo.http import request


class Mtd(http.Controller):

    @http.route('/mtd/<string:message>', auth='user')
    def redirect(self, **kw):
        if kw.get('message') == 'Success':
            request.env['mtd.connection'].get_token()
            return 'Success! you can close the HMRC Page.'
        else:
            return 'Failed! Something went wrong.'

    @http.route('/web/mtd/js', type='json', auth="user")
    def save_js_parameters(self, js_user_agent, window_size, screens):
        request.env['mtd.fraud.prevention'].set_java_script_headers({
            'js_user_agent': js_user_agent,
            'window_size':window_size,
            'screens': window_size
            })

