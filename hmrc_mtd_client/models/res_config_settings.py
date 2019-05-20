# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
import os
import ssl
from odoo.exceptions import UserError

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    login = fields.Char('Name', help='Account name of mtd')
    password = fields.Char('Password', help='Account password of mtd')
    server = fields.Char('Server')
    db = fields.Char('Database')
    port = fields.Char('Port')
    token = fields.Char('token')
    is_sandbox = fields.Boolean('Enable sandbox', help='Enable sandbox environment on HMRC API', default=False)
    submission_period = fields.Selection([('monthly', 'Monthly'), ('quaterly', 'Quaterly'), ('annual', 'Annual')], string="Period")
    is_set_old_journal = fields.Boolean(string='Is set old journals', default=False)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    fuel_debit_account_id = fields.Many2one('account.account', string='Debit account', related='company_id.fuel_debit_account_id')
    fuel_credit_account_id = fields.Many2one('account.account', string='Credit account', related='company_id.fuel_credit_account_id')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        login = params.get_param('mtd.login', default=False)
        password = params.get_param('mtd.password', default=False)
        token = params.get_param('mtd.token', default=False)
        is_sandbox = params.get_param('mtd.sandbox', default=False)
        period = params.get_param('mtd.submission_period', default=False)
        is_set_old_journal = params.get_param('mtd.is_set_old_journal', default=False)
        res.update(
            login=login,
            password=password,
            token=token,
            is_sandbox=is_sandbox,
            submission_period=period,
            is_set_old_journal=is_set_old_journal
        )
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('mtd.login', self.login)
        set_param('mtd.password', self.password)
        set_param('mtd.sandbox', self.is_sandbox)
        set_param('mtd.submission_period', self.submission_period)

    @api.multi
    def get_authorization(self):
        return self.env['mtd.connection'].get_authorization()

    @api.multi
    def vat_formula(self):
        view = self.env.ref('hmrc_mtd_client.vat_calculation_formula_view')

        return {
            'name': 'VAT Formula',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'res.config.settings',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': {
                    'default_box1_formula': "sum([vat_ST0,vat_ST1,vat_ST2,vat_ST11]) + fuel_vat + bad_vat",
                    'default_box2_formula': "sum([vat_PT8M])",
                    'default_box4_formula': "sum([vat_PT11,vat_PT5,vat_PT2,vat_PT1,vat_PT0]) + sum([vat_credit_PT8R,vat_debit_PT8R])",
                    'default_box6_formula': "sum([net_ST0,net_ST1,net_ST2,net_ST11]) + sum([net_ST4]) + fuel_net + bad_net",
                    'default_box7_formula': "sum([net_PT11,net_PT0,net_PT1,net_PT2,net_PT5]) + sum([net_PT7,net_PT8])",
                    'default_box8_formula': "sum([net_ST4])",
                    'default_box9_formula': "sum([net_PT7, net_PT8])"
                }
            }
