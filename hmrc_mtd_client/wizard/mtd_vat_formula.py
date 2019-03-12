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

    box1_formula = fields.Char('Formula')
    box2_formula = fields.Char('Formula')
    box4_formula = fields.Char('Formula')
    box6_formula = fields.Char('Formula')
    box7_formula = fields.Char('Formula')
    box8_formula = fields.Char('Formula')
    box9_formula = fields.Char('Formula')

    @api.model
    def get_values(self):
        res = super(MtdCalculationFormula, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        box1_formula = params.get_param(
            'mtd.box1_formula', default="sum([vat_ST0,vat_ST1,vat_ST2,vat_ST11]) + fuel_vat + bad_vat")
        box2_formula = params.get_param(
            'mtd.box2_formula', default="sum([PT8M])")
        box4_formula = params.get_param(
            'mtd.box4_formula', default="sum([vat_PT11,vat_PT5,vat_PT2,vat_PT1,vat_PT0]) + sum([credit_PT8R,debit_PT8R])")
        box6_formula = params.get_param(
            'mtd.box6_formula', default="-sum([net_ST0,net_ST1,net_ST2,net_ST11]) + sum([net_ST4]) + fuel_net + bad_net")
        box7_formula = params.get_param(
            'mtd.box7_formula', default="sum([net_PT11,net_PT0,net_PT1,net_PT2,net_PT5]) + sum([net_PT7,net_PT8])")
        box8_formula = params.get_param(
            'mtd.box8_formula', default="sum([net_ST4])")
        box9_formula = params.get_param(
            'mtd.box9_formula', default="sum([net_PT7, net_PT8])")
        res.update(
            box1_formula=box1_formula,
            box2_formula=box2_formula,
            box4_formula=box4_formula,
            box6_formula=box6_formula,
            box7_formula=box7_formula,
            box8_formula=box8_formula,
            box9_formula=box9_formula)
        return res

    @api.multi
    def set_values(self):
        super(MtdCalculationFormula, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('mtd.box1_formula', self.box1_formula)
        set_param('mtd.box2_formula', self.box2_formula)
        set_param('mtd.box4_formula', self.box4_formula)
        set_param('mtd.box6_formula', self.box6_formula)
        set_param('mtd.box7_formula', self.box7_formula)
        set_param('mtd.box8_formula', self.box8_formula)
        set_param('mtd.box9_formula', self.box9_formula)

    def submit_formula(self):
        self.set_values()
        formula = {
            'box1': self.box1_formula,
            'box2': self.box2_formula,
            'box4': self.box4_formula,
            'box6': self.box6_formula,
            'box7': self.box7_formula,
            'box8': self.box8_formula,
            'box9': self.box9_formula
        }
        self.test_formula(formula)
        conn = self.env['mtd.connection'].open_connection_odoogap()
        response = conn.execute('mtd.operations', 'submit_formula', formula)
        if response.get('status') == 200:
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
        account_taxes = self.env['account.tax'].search([('active', '=', True)])
        dummy_dict = {}
        for tax in account_taxes:
            dummy_dict.update({
                'vat_%s' % tax.description: 1,
                'net_%s' % tax.description: 1,
                'credit_%s' % tax.description: 1,
                'debit_%s' % tax.description: 1})
        dummy_dict.update({'fuel_net': 1, 'fuel_vat': 1,
                           'bad_net': 1, 'bad_vat': 1})
        return dummy_dict

    def test_formula(self, formula):
        try:
            dummy_dict = self.get_dummy_dict()
            for parameter in formula:
                safe_eval(formula.get(parameter), dummy_dict)
        except Exception as ex:
            raise UserError(msgfy.to_error_message(ex,"{error_msg}").split(':')[1])