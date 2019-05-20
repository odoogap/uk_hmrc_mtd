# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api
from odoo.exceptions import UserError, RedirectWarning


class MTDFuelScaleWizard(models.TransientModel):
    _name = 'mtd.fuel.scale.wizard'
    _description = 'Fuel Scale Wizard'

    @api.multi
    def _get_default_journal(self):
        return self.env['account.journal'].search([('name', '=', 'Miscellaneous Operations')], limit=1).id

    @api.multi
    def _get_submission_period(self):
        return self.env['ir.config_parameter'].sudo().search([('key', '=', 'mtd.submission_period')]).value

    reason = fields.Char(string='Justification', default='Fuel scale charge')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, default=_get_default_journal, domain=[('type', '=', 'general')])
    date = fields.Date(required=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    co2_band = fields.Many2one('mtd.fuel.scale', string='CO2 Band')
    vat_fuel_scale_charge = fields.Monetary(currency_field='company_currency_id', related='co2_band.vat_fuel_scale_charge')
    vat_period_charge = fields.Monetary(currency_field='company_currency_id' , related='co2_band.vat_period_charge')
    vat_exclusive_period_charge = fields.Monetary(currency_field='company_currency_id', related='co2_band.vat_exclusive_period_charge')
    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    submission_period = fields.Char(string='Submission Period', default=_get_submission_period)
    fuel_scale_charge_date = fields.Date(string="Fuel scale charge date")

    def set_fuel_scale_charge_date(self):
        if not self.env.user.company_id.fuel_debit_account_id and not self.env.user.company_id.fuel_credit_account_id:
            raise UserError('Please set up the debit and credit accounts for fuel scale charge.')

        view = self.env.ref('hmrc_mtd_client.fuel_scale_date_form_wizard')
        return {
                'name': 'Fuel scale charge date',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mtd.fuel.scale.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new'
            }

    def get_fuel_scale_table(self):
        return self.env['mtd.fuel.scale'].get_fuel_scale_values(self.fuel_scale_charge_date)

    def _compute_amount(self):
        self.amount = self.vat_fuel_scale_charge

    @api.multi
    def _create_move(self):
        adjustment_type = self.env.context.get('adjustment_type', (self.vat_fuel_scale_charge > 0.0 and 'debit' or 'credit'))
        fuel_scale_charge_tax = self.env['account.tax'].search([('name', '=', 'Fuel scale charge[FCS]')])

        debit_vals = {
            'name': self.reason,
            'debit': abs(self.vat_fuel_scale_charge),
            'credit': 0.0,
            'account_id': self.env.user.company_id.fuel_debit_account_id.id,
            'tax_line_id': adjustment_type == 'debit' and False
        }

        credit_vals = {
            'name': self.reason,
            'debit': 0.0,
            'credit': abs(self.vat_exclusive_period_charge),
            'account_id': self.env.user.company_id.fuel_credit_account_id.id,
            'tax_ids': [(4, fuel_scale_charge_tax.id)]
        }

        credit_vals_tax = {
            'name': self.reason,
            'debit': 0.0,
            'credit': abs(self.vat_period_charge),
            'account_id': self.env.user.company_id.fuel_credit_account_id.id,
            'tax_line_id': fuel_scale_charge_tax.id
        }

        vals = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'state': 'draft',
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals), (0, 0, credit_vals_tax)]
        }

        move = self.env['account.move'].create(vals)
        move.post()
        return move.id

    def create_move(self):
        move_id = self._create_move()
        action = self.env.ref(self.env.context.get('action', 'account.action_move_line_form'))
        result = action.read()[0]
        result['views'] = [(False, 'form')]
        result['res_id'] = move_id
        return result
