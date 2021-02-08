# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models, tools, _

class Company(models.Model):
    _inherit = "res.company"

    vrn = fields.Char('VRN', compute='_compute_vrn', store=True)
    submitted_formula = fields.Boolean('submitted formula', default=False)
    formula = fields.Char('formula', default=False)

    @api.depends('vat')
    def _compute_vrn(self):
        for rec in self:
            vrn = ""
            if rec.vat:
                for number in rec.vat:
                    if number.isdigit():
                        vrn += number
                rec.vrn = vrn
