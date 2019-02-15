# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_mtd_submitted = fields.Boolean('mtd state', default=False)
