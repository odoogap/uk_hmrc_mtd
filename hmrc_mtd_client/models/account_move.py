# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    is_mtd_submitted = fields.Boolean('mtd state', default=False)
    vat_report_id = fields.Many2one('mtd.vat.report', 'VAT Report')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_mtd_submitted = fields.Boolean(
        'mtd state', default=False, related='move_id.is_mtd_submitted', store=True, readonly=True)
