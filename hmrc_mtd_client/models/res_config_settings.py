# -*- coding: utf-8 -*-

import requests
import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    login = fields.Char('Name', help='Account name of mtd')
    password = fields.Char('Password', help='Account password of mtd')
    server = fields.Char('Server')
    test_server = fields.Char('Test Server')
    db = fields.Char('Database')
    port = fields.Char('Port')
    token = fields.Char('token')
    is_sandbox = fields.Boolean('Enable sandbox', help='Enable sandbox environment on HMRC API', default=False)
    submission_period = fields.Selection([('monthly', 'Monthly'), ('quaterly', 'Quarterly'), ('annual', 'Annual')], string="Period")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company.id)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        login = params.get_param('mtd.login', default=False)
        password = params.get_param('mtd.password', default=False)
        token = params.get_param('mtd.token', default=False)
        is_sandbox = params.get_param('mtd.sandbox', default=False)
        period = params.get_param('mtd.submission_period', default=False)
        res.update(
            login=login,
            password=password,
            token=token,
            is_sandbox=is_sandbox,
            submission_period=period,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('mtd.login', self.login)
        set_param('mtd.password', self.password)
        set_param('mtd.sandbox', self.is_sandbox)
        set_param('mtd.submission_period', self.submission_period)

    def get_authorization(self):
        return self.env['mtd.connection'].get_authorization()

    def json_pretty(self, request):
        complete_str = '[%s]' % request
        parsed = json.loads(complete_str)
        return json.dumps(parsed, indent=4, sort_keys=True)

    def test_headers(self):
        params = self.env['ir.config_parameter'].sudo()
        is_sandbox = params.get_param('mtd.sandbox', default=False)

        if is_sandbox:
            api_token = params.get_param('mtd.token', default=False)
            test_hmrc_url = params.get_param('mtd.test_server', default=False)

            url = '%s/test/fraud-prevention-headers/validate' % test_hmrc_url
            req_headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.hmrc.1.0+json',
                'Authorization': 'Bearer %s' % api_token
            }
            prevention_headers = self.env['mtd.fraud.prevention'].create_fraud_prevention_headers()
            req_headers.update(prevention_headers)
            response = requests.get(url, headers=req_headers)
            view = self.env.ref('hmrc_mtd_client.pop_up_message_view')

            return {
                'name': 'Message',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.up.message',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': {
                    'default_name': 'Status:%s\nContent:%s' % (
                        response.status_code, self.json_pretty(response._content.decode("utf-8"))),
                    'delay': True,
                    'no_delay': False
                }
            }
        else:
            raise UserError("Must be in sandbox environment to test the headers.\n"
                            "This Feature is used for development purposes.")

    def vat_formula(self):
        view = self.env.ref('hmrc_mtd_client.vat_calculation_formula_views')

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
                'default_box1_formula': "sum([vat_ST1,vat_ST2,vat_ST11]) + fuel_vat + bad_vat",
                'default_box2_formula': "sum([vat_PT8M])",
                'default_box4_formula': "sum([vat_PT11,vat_PT5,vat_PT2,vat_PT1,vat_PT0]) + sum([vat_credit_PT8R,vat_debit_PT8R])",
                'default_box6_formula': "sum([net_ST0,net_ST1,net_ST2,net_ST11]) + sum([net_ST4]) + fuel_net + bad_net",
                'default_box7_formula': "sum([net_PT11,net_PT0,net_PT1,net_PT2,net_PT5]) + sum([net_PT7,net_PT8])",
                'default_box8_formula': "sum([net_ST4])",
                'default_box9_formula': "sum([net_PT7, net_PT8])"
            }
        }