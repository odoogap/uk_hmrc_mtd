# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class Mtd(http.Controller):

    @http.route('/mtd/<string:message>', auth='user')
    def redirect(self, **kw):
        if kw.get('message') == 'Success':
            request.env['mtd.connection'].get_token()
            return 'Success! you can close the HMRC Page'
        else:
            return 'Failed! Something went wrong'
