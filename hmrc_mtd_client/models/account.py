# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tag_ids = fields.Many2one('account.account.tag', string='Tags', help="Optional tags you may want to assign for custom reporting")
