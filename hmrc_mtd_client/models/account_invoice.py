# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models, _


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    mtd_date = fields.Date('Mtd date', compute='_compute_mtd_date', search="_search_mtd_date")
    net_amount_total = fields.Monetary(string='Amount Net', currency_field='company_currency_id',
                                       compute='_compute_net_amount')
    vat_amount_total = fields.Monetary(string='Amount VAT', currency_field='company_currency_id',
                                       compute='_compute_vat_amount')
    reverse_vat_amount = fields.Monetary(string='Reverse VAT', currency_field='company_currency_id',
                                         compute='_compute_reverse_vat_amount')

    @api.multi
    def _compute_mtd_date(self):
        for record in self:
            record.mtd_date = self._context.get('mtd_date')

    @api.multi
    def _search_mtd_date(self, operator, value):
        mtd = fields.Date.from_string(self._context.get('mtd_date'))
        recs = self.search([('date_invoice', '<', mtd)]).ids
        return [('id', 'in', recs)]

    @api.one
    @api.depends('amount_untaxed')
    def _compute_net_amount(self):
        if self.type in ['out_refund', 'in_refund']:
            self.net_amount_total = - self.amount_untaxed
        else:
            self.net_amount_total = self.amount_untaxed

    @api.one
    @api.depends('amount_tax')
    def _compute_vat_amount(self):
        if self.type in ['out_refund', 'in_refund']:
            self.vat_amount_total = - self.amount_tax
        else:
            self.vat_amount_total = self.amount_tax

    @api.one
    def _compute_reverse_vat_amount(self):
        self.reverse_vat_amount = sum(
            tax_line.amount_total for tax_line in self.tax_line_ids if tax_line.tax_id.description == 'PT8M')
