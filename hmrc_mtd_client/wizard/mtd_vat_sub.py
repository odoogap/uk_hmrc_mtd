# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo import exceptions, _
from odoo.exceptions import UserError, RedirectWarning
import ssl
import os
import json
import requests
import time
import datetime
import logging
import threading

_logger = logging.getLogger(__name__)

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


class MtdVat(models.TransientModel):
    _name = 'mtd.vat.sub'

    def get_periods(self):
        params = self.env['ir.config_parameter'].sudo()
        api_token = params.get_param('mtd.token', default=False)
        hmrc_url = params.get_param('mtd.hmrc.url', default=False)
        token_expire_date = params.get_param('mtd.token_expire_date')

        if api_token:
            if float(token_expire_date) - time.time() < 0:
                api_token = self.env['mtd.connection'].refresh_token()
            if self.env.user.company_id.vat:
                response = requests.get(
                    hmrc_url + '/organisations/vat/' + str(self.env.user.company_id.vrn) + '/obligations',
                    headers={'Content-Type': 'application/json',
                             'Accept': 'application/vnd.hmrc.1.0+json', 'Authorization': 'Bearer ' + api_token},
                    params={"to": time.strftime("%Y-%m-%d"),
                            "from": "%s-%s-%s" % (datetime.datetime.now().year, '01', '01')})
                if response.status_code == 200:
                    message = json.loads(response._content.decode("utf-8"))
                    periods = []
                    for value in message['obligations']:
                        if value['status'] == 'O':
                            periods.append(('18A2:2019/01/08 - 2019/01/31', '2019/01/08 - 2019/01/31'))
                    self._context.update({'periods': periods})
                    view = self.env.ref('hmrc_mtd_client.view_mtd_vat_form')
                    return {'name': 'Calculate VAT', 'type': 'ir.actions.act_window', 'view_type': 'form',
                            'view_mode': 'form', 'res_model': 'mtd.vat.sub', 'views': [(view.id, 'form')],
                            'view_id': view.id, 'target': 'new', 'context': self._context}
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

    def _get_context_periods(self):
        return self._context.get('periods')

    date_from = fields.Date('Invoice date from')
    date_to = fields.Date('Invoice date to')
    period = fields.Selection(_get_context_periods, string='Period')
    vat_scheme = fields.Selection([('AC', 'Accrual Basis')], default='AC', string='VAT scheme')
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    fuel_vat = fields.Monetary('Fuel VAT', currency_field='currency_id')
    fuel_base = fields.Monetary('Fuel Net', currency_field='currency_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    bad_vat = fields.Monetary('Bad VAT', currency_field='currency_id')
    bad_base = fields.Monetary('Bad Net', currency_field='currency_id')

    def get_tax_moves(self, date_to, vat_scheme):
        response = self.env['mtd.connection'].open_connection_odoogap().execute(
            'mtd.operations', 'get_payload', vat_scheme)
        channel_id = self.env.ref('hmrc_mtd_client.channel_mtd')
        if response.get('status') == 200:
            account_taxes = self.env['account.tax'].search([])
            if vat_scheme == 'CB':
                user_types = self.env['account.account.type'].search([('type', 'in', ('receivable', 'payable'))]).ids
                params = [tuple(user_types), date_to, self.env.user.company_id.id, tuple(user_types),
                          date_to, self.env.user.company_id.id, tuple(user_types), date_to,
                          self.env.user.company_id.id, tuple(user_types), 0, date_to,
                          self.env.user.company_id.id]
            else:
                params = [0, date_to, self.env.user.company_id.id]
            data = {'tax_line': [], 'tax_lines': []}
            for account_tax in account_taxes:
                if vat_scheme == 'CB':
                    params[10] = account_tax.id
                else:
                    params[0] = account_tax.id
                self.env.cr.execute(response.get('message').get('tax_line'), params)
                results = self.env.cr.dictfetchall()
                results[0].update({'tag_line_id': [tag.name for tag in account_tax.tag_ids]})
                data['tax_line'].append(results[0])
                self.env.cr.execute(response.get('message').get('tax_lines'), params)
                results = self.env.cr.dictfetchall()
                results[0].update({'tag_tax_ids': [tag.name for tag in account_tax.tag_ids]})
                data['tax_lines'].append(results[0])
            data.update({'status': 'OK'})
            return data
        else:
            _logger.error('Response from server : \n status: ' + str(response.get('status')) + '\n message: ' +
                          response.get('message'))
            channel_id.message_post('Attempt to run vat calculation failed')
            return response

    def vat_thread_calculation(self):
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            channel_id = self.env.ref('hmrc_mtd_client.channel_mtd')
            try:
                submit_data = self.get_tax_moves(self.period.split('-')[1].replace('/', '-'), self.vat_scheme)
                if submit_data.get('status') == 'OK':
                    submit_data.update(
                        {'fuel_vat': self.fuel_vat, 'fuel_base': self.fuel_base})
                    # submit_data.update(self.calculate_bad_debt())
                    response = self.env['mtd.connection'].open_connection_odoogap().execute('mtd.operations',
                                                                                            'calculate_boxes',
                                                                                            submit_data)
                    if response.get('status') == 200:
                        channel_id.message_post(body='The VAT calculation was successfull', message_type="notification",
                                                subtype="mail.mt_comment")
                        self.env['mtd.vat.report'].search(
                            [('name', '=', self.period.split(':')[1])]).unlink()
                        self.env['mtd.vat.report'].create({'registration_number': self.env.user.company_id.vat,
                                                           'vat_scheme': 'Accrual Basis ' if self.vat_scheme == 'AC'
                                                           else 'Cash Basis',
                                                           'name': self.period.split(':')[1],
                                                           'box_one': float(response.get('message').get('box_one')),
                                                           'box_two': float(response.get('message').get('box_two')),
                                                           'box_three': float(response.get('message').get('box_three')),
                                                           'box_four': float(response.get('message').get('box_four')),
                                                           'box_five': float(response.get('message').get('box_five')),
                                                           'box_six': float(response.get('message').get('box_six')),
                                                           'box_seven': float(response.get('message').get('box_seven')),
                                                           'box_eight': float(response.get('message').get('box_eight')),
                                                           'box_nine': float(response.get('message').get('box_nine')),
                                                           'submission_token': response.get('message').get(
                                                               'submission_token'),
                                                           'period_key': self.period.split(':')[0]})
                    else:
                        channel_id.message_post(
                            body='Response from server : \n status: ' + str(response.get('status')) + '\n message: ' +
                                 response.get('message'), message_type="notification", subtype="mail.mt_comment")
                else:
                    channel_id.message_post(
                        body='Response from server : \n status: ' + str(submit_data.get('status')) + '\n message: ' +
                             submit_data.get('message'), message_type="notification", subtype="mail.mt_comment")
                new_cr.commit()
            except Exception as ex:
                _logger.error('Attempt to run vat calculation failed %s ' % str(ex))
                channel_id.message_post('Attempt to run vat calculation failed')
                self._cr.rollback()
                self._cr.close()

    @api.multi
    def vat_calculation(self):
        if self.env['account.move'].search_count([('is_mtd_submitted', '=', False)]) > 0:

            self.ensure_one()
            taxes = ['ST0', 'ST1', 'ST2', 'ST4', 'PT0', 'PT1', 'PT2', 'PT8', 'PT5', 'PT7', 'ST11', 'PT11', 'PT8M',
                     'PT8R']
            for tax in self.env['account.tax'].search(['|', ('active', '=', False), ('active', '=', True)]):
                if tax.description not in taxes or tax.active is False:
                    raise UserError(
                        'The internal references for the default UK CoA do not exist, or are deactivated please fix this issue first.')

            channel_id = self.env.ref('hmrc_mtd_client.channel_mtd')
            channel_id.message_post(body='The VAT calculation has started please check the channel once is completed',
                                    message_type="notification", subtype="mail.mt_comment")
            t = threading.Thread(target=self.vat_thread_calculation)
            t.start()
            view = self.env.ref('hmrc_mtd_client.pop_up_message_view')
            return {'name': 'Message', 'type': 'ir.actions.act_window', 'view_type': 'form', 'view_mode': 'form',
                    'res_model': 'pop.up.message', 'views': [(view.id, 'form')], 'view_id': view.id,
                    'target': 'new',
                    'context': {'default_name': 'The VAT calculation has started please check MTD channel',
                                'delay': False, 'no_delay': True}}

        else:
            view = self.env.ref('hmrc_mtd_client.pop_up_message_view')
            return {'name': 'Message', 'type': 'ir.actions.act_window', 'view_type': 'form', 'view_mode': 'form',
                    'res_model': 'pop.up.message', 'views': [(view.id, 'form')], 'view_id': view.id,
                    'target': 'new',
                    'context': {
                        'default_name': 'There are no invoices available for submission in the given date range',
                        'delay': True, 'no_delay': False}}