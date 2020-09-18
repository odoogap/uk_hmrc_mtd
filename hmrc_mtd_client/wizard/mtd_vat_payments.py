# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
import json
import requests
import time
import datetime
import logging


_logger = logging.getLogger(__name__)

class MtdVatPayments(models.TransientModel):
    _name = 'mtd.vat.payments'
    _description = "VAT Payments"

    received_date = fields.Date('Received on')
    payment_amount = fields.Monetary('Payed Amount', currency_field='currency_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')

    def get_payments(self):
        """get the info payments from the HMRC API
        Returns:
            [dict] -- [payments tree view]
        """
        params = self.env['ir.config_parameter'].sudo()
        api_token = params.get_param('mtd.token', default=False)
        hmrc_url = params.get_param('mtd.hmrc.url', default=False)

        if api_token:
            if self.env.user.company_id.vat:
                req_url = '%s/organisations/vat/%s/payments' % (hmrc_url, str(self.env.user.company_id.vrn))
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
                    for payment in message.get('payments'):
                        self.create(
                        {
                            'payment_amount': payment.get('amount'),
                            'received_date': payment.get('received')
                        })
                    return {
                        'name': 'Payments',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'tree',
                        'res_model': 'mtd.vat.payments',
                        'view': self.env.ref('hmrc_mtd_client.mtd_vat_payments_tree_view').id,
                        'target': 'current'
                    }
                else:
                    message = json.loads(response._content.decode("utf-8"))
                    raise UserError('An error has occurred : \nstatus: %s \nmessage: %s' %(
                        str(response.status_code),
                        message.get('message')
                    ))
            raise UserError('Please set VAT value for your current company.')
        raise UserError('Please configure MTD.')
