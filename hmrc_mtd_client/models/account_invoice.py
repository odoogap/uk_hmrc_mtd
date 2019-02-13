# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models, _
import datetime

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    mtd_date = fields.Date('Mtd date', compute='_compute_mtd_date', search="_search_mtd_date")
    is_mtd_date_due = fields.Boolean('Mtd date', compute='_get_is_mtd_due', store='True', default=False)
    bad_debt = fields.Boolean('Bad debt', default=False)
    bad_debt_date = fields.Date('Bad debt date', default=False)

    @api.multi
    def _compute_mtd_date(self):
        for record in self:
            record.mtd_date = self._context.get('mtd_date')

    @api.multi
    def _search_mtd_date(self, operator, value):
        mtd = fields.Date.from_string(self._context.get('mtd_date'))
        recs = self.search([('date_invoice', '<', mtd)]).ids
        return [('id', 'in', recs)]

    @api.onchange('bad_debt')
    def calculate_date(self):
        if self.bad_debt is True:
            self.bad_debt_date = datetime.datetime.now()
        else:
            self.move_id.is_mtd_submitted = False

