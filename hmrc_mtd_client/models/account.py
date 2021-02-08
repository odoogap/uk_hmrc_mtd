# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools


class AccountTax(models.Model):
    _inherit = 'account.tax'

    # tag_ids = fields.Char(string='Tags')
    tag_ids = fields.Many2many('account.account.tag', 'account_tax_account_tag', string='Tags', help="Optional tags you may want to assign for custom reporting")
