# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo import exceptions, _
from odoo.exceptions import UserError, RedirectWarning
import json
import requests
import time
import datetime
import logging
import os
import ssl

_logger = logging.getLogger(__name__)


if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


class MtdVatLiabilities(models.TransientModel):
    _name = 'mtd.vat.liabilities'

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
        params = self.env['ir.config_parameter'].sudo()
        api_token = params.get_param('mtd.token', default=False)
        hmrc_url = params.get_param('mtd.hmrc.url', default=False)
        token_expire_date = params.get_param('mtd.token_expire_date')

        if api_token:
            if float(token_expire_date) - time.time() < 0:
                api_token = self.env['mtd.connection'].refresh_token()
            if self.env.user.company_id.vat:
                response = requests.get(
                    '%s/organisations/vat/%s/liabilities' % (hmrc_url, str(self.env.user.company_id.vrn)),
                    headers={'Content-Type': 'application/json',
                             'Accept': 'application/vnd.hmrc.1.0+json', 'Authorization': 'Bearer %s' % api_token,
                             'Gov-Test-Scenario': 'MULTIPLE_LIABILITIES'},
                    params={"to": time.strftime("%Y-%m-%d"),
                            "from": "%s-%s-%s" % (datetime.datetime.now().year, '01', '01')})
                if response.status_code == 200:
                    self.search([]).unlink()
                    message = json.loads(response._content.decode("utf-8"))
                    for liability in message.get('liabilities'):
                        self.create({'tax_period_start': liability.get('taxPeriod').get('from'),
                                     'tax_period_end': liability.get('taxPeriod').get('to'),
                                     'liability_type': liability.get('type'),
                                     'original_amount': liability.get('originalAmount'),
                                     'outstanding_amount': liability.get('outstandingAmount'),
                                     'due_date': liability.get('due')})
                    return {'name': 'Liabilities', 'type': 'ir.actions.act_window',
                            'view_mode': 'tree,form', 'res_model': 'mtd.vat.liabilities',
                            'views': [[self.env.ref('hmrc_mtd_client.mtd_vat_liabilities_tree_view').id, 'list'],
                                      [self.env.ref('hmrc_mtd_client.mtd_vat_liabilities_form_view').id, 'form']],
                            'target': 'current'}
                else:
                    message = json.loads(response._content.decode("utf-8"))
                    raise UserError(
                        'An error has occurred : \nstatus: ' + str(
                            response.status_code) + '\n' + 'message: ' + message.get(
                            'message'))
            raise RedirectWarning('Please set VAT value for your current company',
                                  self.env.ref('base.action_res_company_form').id, _('Go to the configuration panel'))

        raise RedirectWarning('Please configure MTD', self.env.ref('account.res_config_settings_view_form').id,
                              _('Go to the configuration panel'))
