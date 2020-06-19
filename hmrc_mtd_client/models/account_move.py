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

    mtd_date = fields.Date('Mtd date', compute='_compute_mtd_date', search="_search_mtd_date")
    is_mtd_submitted = fields.Boolean('mtd state', default=False, store=True, related='move_id.is_mtd_submitted')

    @api.multi
    def _compute_mtd_date(self):
        for record in self:
            record.mtd_date = self._context.get('mtd_date')

    @api.multi
    def _search_mtd_date(self, operator, value):
        mtd = fields.Date.from_string(self._context.get('mtd_date'))
        res = self.env.cr.execute("""
        SELECT id
        FROM account_move_line
        WHERE date < '%s'""" % mtd)
        res = self.env.cr.fetchall()
        return [('id', 'in', [r[0] for r in res])]
