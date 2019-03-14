# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
import odoorpc
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools.safe_eval import safe_eval
import os
import ssl
import msgfy

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context

class MtdCalculationFormula(models.TransientModel):
    _inherit = 'res.config.settings'

    box_one = fields.Char('Formula')
    box_two = fields.Char('Formula')
    box_four = fields.Char('Formula')
    box_six = fields.Char('Formula')
    box_seven = fields.Char('Formula')
    box_eight = fields.Char('Formula')
    box_nine = fields.Char('Formula')

    @api.model
    def get_values(self):
        res = super(MtdCalculationFormula, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        box_one = params.get_param('mtd.box1_formula', False)
        box_two = params.get_param('mtd.box2_formula', False)
        box_four = params.get_param('mtd.box4_formula', False)
        box_six = params.get_param('mtd.box6_formula', False)
        box_seven = params.get_param('mtd.box7_formula', False)
        box_eight = params.get_param('mtd.box8_formula', False)
        box_nine = params.get_param('mtd.box9_formula', False)
        res.update(
            box_one=box_one,
            box_two=box_two,
            box_four=box_four,
            box_six=box_six,
            box_seven=box_seven,
            box_eight=box_eight,
            box_nine=box_nine)
        return res

    @api.multi
    def set_values(self):
        super(MtdCalculationFormula, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('mtd.box1_formula', self.box_one)
        set_param('mtd.box2_formula', self.box_two)
        set_param('mtd.box4_formula', self.box_four)
        set_param('mtd.box6_formula', self.box_six)
        set_param('mtd.box7_formula', self.box_seven)
        set_param('mtd.box8_formula', self.box_eight)
        set_param('mtd.box9_formula', self.box_nine)

    def submit_formula(self):
        self.set_values()
        attrs = ['box_one','box_two','box_four','box_six','box_seven','box_eight','box_nine']
        formula = {}

        for attr in attrs:
            if getattr(self, attr):
                formula.update({attr:getattr(self, attr)})

        self.test_formula(formula)
        conn = self.env['mtd.connection'].open_connection_odoogap()
        response = conn.execute('mtd.operations', 'submit_formula', formula)
        if response.get('status') == 200:
            self.env.user.company_id.submited_formula = True
            view = self.env.ref('hmrc_mtd_client.pop_up_message_view')
            return {'name': 'Success', 'type': 'ir.actions.act_window', 'view_type': 'form', 'view_mode': 'form',
                    'res_model': 'pop.up.message', 'views': [(view.id, 'form')], 'view_id': view.id,
                    'target': 'new',
                    'context': {
                        'default_name': response.get('message'),
                        'delay': True, 'no_delay': False}}
        raise UserError(
            'An error has occurred : \n status: %s \n message: %s ' % (
                str(response.get('status')), response.get('message')))

    def get_dummy_dict(self):
        account_taxes = self.env['account.tax'].search([('active', '=', True)]).mapped('tag_ids').mapped('name')
        dummy_dict = {}
        for tax in account_taxes:
            dummy_dict.update({
                'vat_%s' % tax: 1,
                'net_%s' % tax: 1,
                'vat_credit_%s' % tax: 1,
                'vat_debit_%s' % tax: 1,
                'net_credit_%s' % tax: 1,
                'net_debit_%s' % tax: 1
                })
        dummy_dict.update({'fuel_net': 1, 'fuel_vat': 1,
                           'bad_net': 1, 'bad_vat': 1})
        return dummy_dict

    def test_formula(self, formula):
        try:
            dummy_dict = self.get_dummy_dict()
            for parameter in formula:
                if formula.get(parameter):
                    if 'sum' in formula.get(parameter) or '+' in formula.get(parameter) or '-' in formula.get(parameter):
                        safe_eval(formula.get(parameter), dummy_dict)
                    else:
                        raise UserError(
                            'Boxes formulas need to have arithmethic operations')
        except Exception as ex:
            raise UserError(msgfy.to_error_message(ex, "{error_msg}"))
