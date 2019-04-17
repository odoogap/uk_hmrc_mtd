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
            return 'Success! you can close the HMRC Page'
        else:
            return 'Failed! Something went wrong'
