# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import requests
import time
import datetime
import logging

_logger = logging.getLogger(__name__)

class MtdVatLiabilities(models.TransientModel):
    _name = 'mtd.vat.liabilities'
    _description = "VAT Liabilites"

    name = fields.Char(default='Liability details')
    tax_period_start = fields.Date('from')
    tax_period_end = fields.Date('To')
    liability_type = fields.Char('Type')
    original_amount = fields.Monetary('Original amount', currency_field='currency_id')
    outstanding_amount = fields.Monetary('Outstanding amount', currency_field='currency_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    due_date = fields.Date('Due')

    def get_liabilities(self):
        """gets the liabilities from HMRC API and returns a tree view with the info
        Returns:
            [dict] -- [liabilities tree view]
        """
        params = self.env['ir.config_parameter'].sudo()
        api_token = params.get_param('mtd.token', default=False)
        hmrc_url = params.get_param('mtd.hmrc.url', default=False)

        if api_token:

            if self.env.user.company_id.vat:
                req_url = '%s/organisations/vat/%s/liabilities' % (hmrc_url, str(self.env.user.company_id.vrn))
                req_headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.hmrc.1.0+json', 
                    'Authorization': 'Bearer %s' % api_token
                }
                prevention_headers = self.env['mtd.fraud.prevention'].create_fraud_prevention_headers()
                req_headers.update(prevention_headers)
                req_params = {
                    "to": time.strftime("%Y-%m-%d"),
                    "from": "%s-%s-%s" % (datetime.datetime.now().year, '01', '01')
                }
                response = requests.get(req_url, headers=req_headers, params=req_params)

                if response.status_code == 200:
                    self.search([]).unlink()
                    message = json.loads(response._content.decode("utf-8"))

                    for liability in message.get('liabilities'):
                        self.create(
                            {
                                'tax_period_start': liability.get('taxPeriod').get('from'),
                                'tax_period_end': liability.get('taxPeriod').get('to'),
                                'liability_type': liability.get('type'),
                                'original_amount': liability.get('originalAmount'),
                                'outstanding_amount': liability.get('outstandingAmount'),
                                'due_date': liability.get('due')
                            })
                    return {
                            'name': 'Liabilities',
                            'type': 'ir.actions.act_window',
                            'view_mode': 'tree,form',
                            'res_model': 'mtd.vat.liabilities',
                            'views': [
                                [self.env.ref('hmrc_mtd_client.mtd_vat_liabilities_tree_view').id, 'list'],
                                [self.env.ref('hmrc_mtd_client.mtd_vat_liabilities_form_view').id, 'form']
                            ],
                            'target': 'current'
                        }
                else:
                    message = json.loads(response._content.decode("utf-8"))
                    raise UserError('An error has occurred:\nstatus: %s\nmessage: %s' % (str(response.status_code), message.get('message')))
            raise UserError('Please set VAT value for your current company.')
        raise UserError('Please configure MTD.')
