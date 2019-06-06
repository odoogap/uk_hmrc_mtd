# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo import exceptions, _
from odoo.exceptions import UserError
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


class MtdHmrcBoxesVerification(models.TransientModel):
    _name = 'mtd.vat.verification'
    _description = "VAT Verification"

    name = fields.Char(default='HMRC VAT', readonly=True)
    vatDueSales = fields.Char(string='Box 1', readonly=True)
    vatDueAcquisitions = fields.Char(string='Box 2', readonly=True)
    totalVatDue = fields.Char(string='Box 3', readonly=True)
    vatReclaimedCurrPeriod = fields.Char(string='Box 4', readonly=True)
    netVatDue = fields.Char(string='Box 5', readonly=True)
    totalValueSalesExVAT = fields.Char(string='Box 6', readonly=True)
    totalValuePurchasesExVAT = fields.Char(string='Box 7', readonly=True)
    totalValueGoodsSuppliedExVAT = fields.Char(string='Box 8', readonly=True)
    totalAcquisitionsExVAT = fields.Char(string='Box 9', readonly=True)

    def verify_submission(self):
        """gets the the return info that is on hmrc
        Returns:
            [dict] -- [vat verification form view]
        """
        params = self.env['ir.config_parameter'].sudo()
        api_token = params.get_param('mtd.token', default=False)
        hmrc_url = params.get_param('mtd.hmrc.url', default=False)
        token_expire_date = params.get_param('mtd.token_expire_date')
        period_key = self._context.get('period_key')
        if api_token:
            if float(token_expire_date) - time.time() < 0:
                api_token = self.env['mtd.connection'].refresh_token()

            if self.env.user.company_id.vat:
                req_url = '%s/organisations/vat/%s/returns/%s' % (hmrc_url, str(self.env.user.company_id.vrn), period_key)
                req_headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.hmrc.1.0+json', 'Authorization': 'Bearer %s' % api_token
                }
                response = requests.get(req_url, headers=req_headers)

                if response.status_code == 200:
                    self.search([]).unlink()
                    message = json.loads(response._content.decode("utf-8"))
                    rec_id = self.create(
                        {
                            'vatDueSales': message.get('vatDueSales'),
                            'vatDueAcquisitions': message.get('vatDueAcquisitions'),
                            'totalVatDue': message.get('totalVatDue'),
                            'vatReclaimedCurrPeriod': message.get('vatReclaimedCurrPeriod'),
                            'netVatDue': message.get('netVatDue'),
                            'totalValueSalesExVAT': message.get('totalValueSalesExVAT'),
                            'totalValuePurchasesExVAT': message.get('totalValuePurchasesExVAT'),
                            'totalValueGoodsSuppliedExVAT': message.get('totalValueGoodsSuppliedExVAT'),
                            'totalAcquisitionsExVAT': message.get('totalAcquisitionsExVAT')
                        })
                    
                    return {
                            'name': 'HMRC VAT Verification',
                            'type': 'ir.actions.act_window',
                            'view_mode': 'form',
                            'res_model': 'mtd.vat.verification',
                            'views': [
                                [self.env.ref('hmrc_mtd_client.mtd_vat_verification_form_view').id, 'form']
                            ],
                            'context':{'active_id': rec_id.id},
                            'res_id': rec_id.id,
                            'target': 'new'
                        }
                else:
                    message = json.loads(response._content.decode("utf-8"))
                    raise UserError('An error has occurred:\nstatus: %s\nmessage: %s' % (str(response.status_code), message.get('message')))
            raise UserError('Please set VAT value for your current company.')
        raise UserError('Please configure MTD.')
