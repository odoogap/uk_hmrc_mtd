# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models, tools, _

class Company(models.Model):
    _inherit = "res.company"

    vrn = fields.Char('VRN', compute='_compute_vrn', store=True)
    submited_formula = fields.Boolean('submited formula', default=False)
    formula = fields.Char('formula', default=False)
    fuel_debit_account_id = fields.Many2one('account.account', string='Debit account')
    fuel_credit_account_id = fields.Many2one('account.account', string='Credit account')

    @api.multi
    @api.depends('vat')
    def _compute_vrn(self):
        for rec in self:
            vrn = ""
            if rec.vat:
                for number in rec.vat:
                    if number.isdigit():
                        vrn += number
                rec.vrn = vrn
