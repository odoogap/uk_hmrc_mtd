# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api


class MTDFuelScaleWizard(models.TransientModel):
    _name = 'mtd.fuel.scale.wizard'
    _description = 'Fuel Scale Wizard'

    @api.multi
    def _get_default_journal(self):
        return self.env['account.journal'].search([('type', '=', 'general')], limit=1).id

    @api.multi
    def _get_submission_period(self):
        return self.env['ir.config_parameter'].sudo().search([('key', '=', 'mtd.submission_period')]).value

    reason = fields.Char(string='Justification', default='Fuel scale charge')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, default=_get_default_journal, domain=[('type', '=', 'general')])
    date = fields.Date(required=True, default=fields.Date.context_today)
    debit_account_id = fields.Many2one('account.account', string='Debit account', required=True, domain=[('deprecated', '=', False)])
    credit_account_id = fields.Many2one('account.account', string='Credit account', required=True, domain=[('deprecated', '=', False)])
    amount = fields.Monetary(currency_field='company_currency_id', compute="_compute_amount")
    co2_band = fields.Many2one('mtd.fuel.scale', string='CO2 Band')
    vat_fuel_scale_charge = fields.Monetary(currency_field='company_currency_id')
    vat_period_charge = fields.Monetary(currency_field='company_currency_id')
    vat_exclusive_period_charge = fields.Monetary(currency_field='company_currency_id')
    adjustment_type = fields.Selection(
        [
            ('debit', 'Applied on debit journal item'),
            ('credit', 'Applied on credit journal item')
        ],
        string="Adjustment Type",
        store=False,
        required=True
    )
    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    submission_period = fields.Char(string='Submission Period', default=_get_submission_period)

    def _compute_amount(self):
        self.amount = self.vat_fuel_scale_charge

    @api.multi
    def _create_move(self):
        adjustment_type = self.env.context.get('adjustment_type', (self.amount > 0.0 and 'debit' or 'credit'))
        fuel_scale_charge_tax = self.env['account.tax'].search([('name', '=', 'Fuel scale charge[FCS]')])

        debit_vals = {
            'name': self.reason,
            'debit': abs(self.amount),
            'credit': 0.0,
            'account_id': self.debit_account_id.id,
            'tax_line_id': adjustment_type == 'debit' and fuel_scale_charge_tax.id or False,
        }
        credit_vals = {
            'name': self.reason,
            'debit': 0.0,
            'credit': abs(self.amount),
            'account_id': self.credit_account_id.id,
            'tax_line_id': adjustment_type == 'credit' and fuel_scale_charge_tax.id or False,
        }
        vals = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'state': 'draft',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        move = self.env['account.move'].create(vals)
        move.post()
        return move.id

    @api.multi
    def create_move_debit(self):
        return self.with_context(adjustment_type='debit').create_move()

    @api.multi
    def create_move_credit(self):
        return self.with_context(adjustment_type='credit').create_move()

    def create_move(self):
        move_id = self._create_move()
        action = self.env.ref(self.env.context.get('action', 'account.action_move_line_form'))
        result = action.read()[0]
        result['views'] = [(False, 'form')]
        result['res_id'] = move_id
        return result

    @api.onchange('co2_band')
    def set_fuel_scale_values(self):
        self.vat_fuel_scale_charge = self.co2_band.vat_fuel_scale_charge
        self.vat_exclusive_period_charge = self.co2_band.vat_exclusive_period_charge
        self.vat_period_charge = self.co2_band.vat_period_charge
