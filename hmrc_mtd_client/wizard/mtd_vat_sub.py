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
import threading
import os
import ssl

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
                    '%s/organisations/vat/%s/obligations' % (
                        hmrc_url, str(self.env.user.company_id.vrn)),
                    headers={'Content-Type': 'application/json',
                             'Accept': 'application/vnd.hmrc.1.0+json', 'Authorization': 'Bearer %s' % api_token},
                    params={"to": time.strftime("%Y-%m-%d"),
                            "from": "%s-%s-%s" % (datetime.datetime.now().year, '01', '01')})
                if response.status_code == 200:
                    message = json.loads(response._content.decode("utf-8"))
                    periods = []
                    for value in message['obligations']:
                        if value['status'] == 'O':
                            periods.append(('%s:%s-%s' % (value.get('periodKey'), '2019-02-01'.replace('-', '/'),
                                                          '2019-02-28'.replace('-', '/')),
                                            '%s - %s' % (
                                                '2019-02-01'.replace('-', '/'),
                                                '2019-02-28'.replace('-', '/'))))
                    self._context.update({'periods': periods})
                    view = self.env.ref('hmrc_mtd_client.view_mtd_vat_form')
                    return {'name': 'Calculate VAT', 'type': 'ir.actions.act_window', 'view_type': 'form',
                            'view_mode': 'form', 'res_model': 'mtd.vat.sub', 'views': [(view.id, 'form')],
                            'view_id': view.id, 'target': 'new', 'context': self._context}
                else:
                    message = json.loads(response._content.decode("utf-8"))
                    raise UserError(
                        'An error has occurred : \n status: %s \n message: %s' % (
                            str(response.status_code), message.get('message')))

            raise UserError('Please set VAT value for your current company.')

        raise UserError('Please configure MTD.')

    def _get_context_periods(self):
        return self._context.get('periods')

    date_from = fields.Date('Invoice date from')
    date_to = fields.Date('Invoice date to')
    period = fields.Selection(_get_context_periods, string='Period')
    vat_scheme = fields.Selection(
        [('AC', 'Accrual Basis')], default='AC', string='VAT scheme')
    currency_id = fields.Many2one(
        'res.currency', string='Currency', related='company_id.currency_id')
    fuel_vat = fields.Monetary('Fuel VAT', currency_field='currency_id')
    fuel_base = fields.Monetary('Fuel Net', currency_field='currency_id')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.user.company_id)
    bad_vat = fields.Monetary('Bad VAT', currency_field='currency_id')
    bad_base = fields.Monetary('Bad Net', currency_field='currency_id')

    def dict_refactor(self, data):
        new_dict = {}
        for tax in data.get('tax_line'):
            new_dict.update({
                'vat_%s' % str(tax.get('tag_line_id')[0]): tax.get('vat'),
                'vat_credit_%s' % str(tax.get('tag_line_id')[0]): tax.get('credit'),
                'vat_debit_%s' % str(tax.get('tag_line_id')[0]): tax.get('debit')})
        for tax in data.get('tax_lines'):
            new_dict.update({
                'net_%s' % str(tax.get('tag_tax_ids')[0]): tax.get('net'),
                'net_credit_%s' % str(tax.get('tag_tax_ids')[0]): tax.get('credit'),
                'net_debit_%s' % str(tax.get('tag_tax_ids')[0]): tax.get('debit')})
        return new_dict

    def get_tax_moves(self, date_to, vat_scheme):
        response = self.env['mtd.connection'].open_connection_odoogap().execute(
            'mtd.operations', 'get_payload', vat_scheme)
        channel_id = self.env.ref('hmrc_mtd_client.channel_mtd')
        if response.get('status') == 200:
            account_taxes = self.env['account.tax'].search(
                [('active', '=', True)])
            if vat_scheme == 'AC':
                params = [0, date_to, self.env.user.company_id.id]
            data = {'tax_line': [], 'tax_lines': []}
            for account_tax in account_taxes:
                if vat_scheme == 'AC':
                    params[0] = account_tax.id
                self.env.cr.execute(response.get(
                    'message').get('tax_line'), params)
                results = self.env.cr.dictfetchall()
                results[0].update(
                    {'tag_line_id': [tag.name for tag in account_tax.tag_ids]})
                data['tax_line'].append(results[0])
                self.env.cr.execute(response.get(
                    'message').get('tax_lines'), params)
                results = self.env.cr.dictfetchall()
                results[0].update(
                    {'tag_tax_ids': [tag.name for tag in account_tax.tag_ids]})
                data['tax_lines'].append(results[0])
            return self.dict_refactor(data)
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
                submit_data = self.get_tax_moves(self.period.split(
                    '-')[1].replace('/', '-'), self.vat_scheme)
                submit_data.update(
                    {'fuel_vat': self.fuel_vat, 'bad_vat': self.bad_vat, 'fuel_net': self.fuel_base, 'bad_net': self.bad_base})
                response = self.env['mtd.connection'].open_connection_odoogap().execute(
                    'mtd.operations', 'calculate_boxes', submit_data)
                if response.get('status') == 200:
                    channel_id.message_post(body='The VAT calculation was successfull.',
                                            message_type="notification", subtype="mail.mt_comment")
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
                                                       'submission_token': response.get('message').get('submission_token'),
                                                       'period_key': self.period.split(':')[0]})
                else:
                    channel_id.message_post(body='Response from server : \n status: %s\n message: %s' % (str(response.get(
                        'status')), response.get('message')), message_type="notification", subtype="mail.mt_comment")
                new_cr.commit()
            except Exception as ex:
                self._cr.rollback()
                _logger.error(
                    'Attempt to run vat calculation failed %s ' % str(ex))
                channel_id.message_post('Attempt to run vat calculation failed.',
                                        message_type="notification", subtype="mail.mt_comment")
                new_cr.commit()
                self._cr.close()

    def _sql_get_move_lines_count(self):
        return """
            SELECT count(account_move.id) FROM account_move
            INNER JOIN account_move_line ON account_move_line.move_id = account_move.id
            INNER JOIN account_move_line_account_tax_rel ON account_move_line.id =
            account_move_line_account_tax_rel.account_move_line_id INNER JOIN
            account_tax ON account_tax.id = account_move_line_account_tax_rel.account_tax_id
            WHERE account_move.state = 'posted'  AND
            account_move.is_mtd_submitted = 'f'  AND
            account_move.company_id in (%s)
        """

    @api.multi
    def vat_calculation(self):
        if self.env.user.company_id.submited_formula:
            self.env.cr.execute(self._sql_get_move_lines_count() % self.env.user.company_id.id)
            results = self.env.cr.dictfetchall()
            if results[0].get('count') > 0:
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
        else:
            raise UserError('Please submit the VAT formula first.')
