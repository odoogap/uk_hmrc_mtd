# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

import os
import ssl
import msgfy

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools.safe_eval import safe_eval

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None)): ssl._create_default_https_context = ssl._create_unverified_context


class MtdCalculationFormula(models.TransientModel):
    _inherit = 'res.config.settings'

    box_one = fields.Char('Box One Formula')
    box_two = fields.Char('Box Two Formula')
    box_four = fields.Char('Box Three Formula')
    box_six = fields.Char('Box Six Formula')
    box_seven = fields.Char('Box Seven Formula')
    box_eight = fields.Char('Box Eight Formula')
    box_nine = fields.Char('Box Nine Formula')

    @api.model
    def get_values(self):
        res = super(MtdCalculationFormula, self).get_values()
        params = self.env['ir.config_parameter'].sudo()

        box_one = params.get_param('mtd.box_one_formula', 'sum([vat_ST1,vat_ST2,vat_ST11])')
        box_two = params.get_param('mtd.box_two_formula', 'sum([vat_PT8M])')
        box_four = params.get_param('mtd.box_four_formula', 'sum([vat_PT11,vat_PT5,vat_PT2,vat_PT1,vat_PT0]) + sum([vat_credit_PT8R,vat_debit_PT8R])')
        box_six = params.get_param('mtd.box_six_formula', 'sum([net_ST0,net_ST1,net_ST2,net_ST11]) + sum([net_ST4])')
        box_seven = params.get_param('mtd.box_seven_formula', 'sum([net_PT11,net_PT0,net_PT1,net_PT2,net_PT5]) + sum([net_PT7,net_PT8])')
        box_eight = params.get_param('mtd.box_eight_formula', 'sum([net_ST4])')
        box_nine = params.get_param('mtd.box_nine_formula', 'sum([net_PT7, net_PT8])')
        res.update(
            box_one=box_one,
            box_two=box_two,
            box_four=box_four,
            box_six=box_six,
            box_seven=box_seven,
            box_eight=box_eight,
            box_nine=box_nine
        )
        return res

    def set_values(self):
        super(MtdCalculationFormula, self).set_values()
        set_param = self.env['ir.config_parameter'].sudo().set_param
        attrs = ['box_one', 'box_two', 'box_four', 'box_six', 'box_seven', 'box_eight', 'box_nine']
        replace_items = [
            'sum([', '])', '+', '-',
            'vat_credit_', 'net_credit_', 'vat_debit_', 'net_debit_', 'net_', 'vat_', ','
        ]  # items that should be replaced in the formula in order to get the taxes tag
        box_three_taxes = []
        box_five_taxes = []

        for attr in attrs:
            if getattr(self, attr):
                set_param('mtd.%s_formula' % attr, getattr(self, attr))
                box_taxes = getattr(self, attr)

                for item in replace_items:
                    if item == ',':
                        box_taxes = box_taxes.strip()
                        box_taxes = box_taxes.replace(item, ' ')  # replace ',' with ' ' for split
                        box_taxes = box_taxes.split()  # convert string into list
                        box_taxes = list(dict.fromkeys(box_taxes))  # remove duplicated entries
                    else:
                        box_taxes = box_taxes.replace(item, '')

                set_param('mtd.%s_taxes' % attr, str(box_taxes))
                if attr == 'box_one' or attr == 'box_two':
                    box_three_taxes.extend(box_taxes)
                    box_five_taxes.extend(box_taxes)
                if attr == 'box_four':
                    box_five_taxes.extend(box_taxes)
            else:
                set_param('mtd.%s_taxes' % attr, 'N/A')

        if box_five_taxes:
            box_five_taxes = list(dict.fromkeys(box_five_taxes))  # remove duplicated entries
            set_param('mtd.box_five_taxes', str(box_five_taxes))

        if box_three_taxes:
            box_three_taxes = list(dict.fromkeys(box_three_taxes))  # remove duplicated entries
            set_param('mtd.box_three_taxes', str(box_three_taxes))

    def submit_formula(self):
        """allows the submission off the formula to the server
        Returns:
            [dict] -- [popup message]
        """
        self.set_values()
        attrs = ['box_one', 'box_two', 'box_four', 'box_six', 'box_seven', 'box_eight', 'box_nine']
        formula = {}

        for attr in attrs:
            if getattr(self, attr):
                if getattr(self, attr) != 'N/A':
                    formula.update({attr: getattr(self, attr)})

        self.test_formula(formula)
        conn = self.env['mtd.connection'].open_connection_odoogap()
        response = conn.submit_formula(formula)

        if response.get('status') == 200:
            self.env.company.submitted_formula = True
            view = self.env.ref('hmrc_mtd_client.pop_up_message_view')

            return {
                'name': 'Success',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.up.message',
                'views': [
                    (view.id, 'form')
                ],
                'view_id': view.id,
                'target': 'new',
                'context': {
                    'default_name': response.get('message'),
                    'delay': True,
                    'no_delay': False
                }
            }
        raise UserError('An error has occurred : \n status: %s \n message: %s ' % (str(response.get('status')), response.get('message')))

    def get_dummy_dict(self):
        """creates a dummy dict to ensure that the formula is correctly configured
        Returns:
            [dict] -- [dummy dict with the formula keys]
        """
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

        return dummy_dict

    def test_formula(self, formula):
        """tests the formula with the dummy dict
        Arguments:
            formula {dict} -- [formula dummy dict]
        """
        try:
            dummy_dict = self.get_dummy_dict()
            for parameter in formula:
                if formula.get(parameter):

                    if formula.get(parameter) != 'N/A':
                        if 'sum' in formula.get(parameter) or '+' in formula.get(parameter) or '-' in formula.get(
                                parameter):
                            safe_eval(formula.get(parameter).encode('utf8'), dummy_dict)

                        else:
                            raise UserError('Boxes formulas need to have arithmethic operations.')

        except Exception as ex:
            raise UserError(msgfy.to_error_message(ex, "{error_msg}"))
