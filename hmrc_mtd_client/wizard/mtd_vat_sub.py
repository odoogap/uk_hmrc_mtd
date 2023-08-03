# -*- coding: utf-8 -*-

import json
import requests
import time
import datetime
import threading
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning

_logger = logging.getLogger(__name__)


class MtdVat(models.TransientModel):
    _name = 'mtd.vat.sub'
    _description = "VAT Calculation"

    def check_credits(self):
        response = self.env['mtd.connection'].open_connection_odoogap().check_credits()
        if response.get('status') != 200:
            raise UserError(response.get('message'))

    def check_version(self):
        latest_version = self.env['ir.module.module'].search([('name', '=', 'hmrc_mtd_client')]).latest_version
        values = {
            'odoo_version': 'v14',
            'mtd_client_version': latest_version
        }

        response = self.env['mtd.connection'].open_connection_odoogap().check_version(values)
        if response.get('status') != 200:
            raise UserError(response.get('message'))

    def request_periods(self, hmrc_url, api_token):
        self.check_credits()
        self.check_version()
        if self.env.company.vat:
            url = '%s/organisations/vat/%s/obligations' % (hmrc_url, str(self.env.company.vrn))
            req_headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/vnd.hmrc.1.0+json',
                    'Authorization': 'Bearer %s' % api_token
                }

            prevention_headers = self.env['mtd.fraud.prevention'].create_fraud_prevention_headers()
            req_headers.update(prevention_headers)

            req_params = {
                    'to': time.strftime("%Y-%m-%d"),
                    'from': "%s-%s-%s" % (datetime.datetime.now().year - 1, datetime.datetime.now().strftime("%m"), datetime.datetime.now().strftime("%d"))
                }
            response = requests.get(url, headers=req_headers, params=req_params)
            if response.status_code == 200:
                message = json.loads(response._content.decode("utf-8"))
                periods = []

                for value in message['obligations']:
                    if value['status'] == 'O':
                        period = '%s:%s-%s' % (value.get('periodKey'), value.get('start').replace('-', '/'),
                                               value.get('end').replace('-', '/'))
                        date = '%s - %s' % (value.get('start').replace('-', '/'), value.get('end').replace('-', '/'))
                        periods.append((period, date))

                self._context.update({'periods': periods})
                view = self.env.ref('hmrc_mtd_client.view_mtd_vat_form')
                return {
                        'name': 'Calculate VAT',
                        'type': 'ir.actions.act_window',
                        'view_type': 'form',
                        'view_mode': 'form',
                        'res_model': 'mtd.vat.sub',
                        'views': [(view.id, 'form')],
                        'view_id': view.id,
                        'target': 'new',
                        'context': self._context
                    }
            else:
                message = json.loads(response._content.decode("utf-8"))
                raise UserError('An error has occurred : \n status: %s \n message: %s' % (str(response.status_code), message.get('message')))

        raise UserError('Please set VAT value for your current company.')

    @api.model
    def get_periods(self):
        """
        gets the periods from the HMRC API
        Returns:
            [dict] -- [returns dict for calculate form view]
        """
        params = self.env['ir.config_parameter'].sudo()
        api_token = params.get_param('mtd.token', default=False)
        hmrc_url = params.get_param('mtd.hmrc.url', default=False)
        is_set_old_journal = params.get_param('mtd.is_set_old_journal', default=False)
        login = params.get_param('mtd.login', default=False)
        password = params.get_param('mtd.password', default=False)

        if not (login or password):
            raise UserError('Your Odoo/MTD credentials are empty! Please go to configuration and fill in the '
                            'parameters, or if you are not signed up, go to our website and request access using the '
                            'contact form!')
        else:
            if not is_set_old_journal:
                raise UserError('Please Set Old Journal')
            if api_token:
                return self.request_periods(hmrc_url, api_token)

            raise UserError('Please configure MTD.')

    def _get_context_periods(self):
        return self._context.get('periods')

    date_from = fields.Date('Invoice date from')
    date_to = fields.Date('Invoice date to')
    period = fields.Selection(_get_context_periods, string='Period')
    vat_scheme = fields.Selection([('AC', 'Accrual Basis')], default='AC', string='VAT scheme')

    def dict_refactor(self, data):
        """
        refactor dict keys for the VAT formula
        Arguments:
            data {dict} -- [info with the move tax values]
        Returns:
            [dict] -- [dict with the refatored values]
        """
        new_dict = {}
        for tax in data.get('tax_line'):
            if tax.get('tag_line_id'):
                new_dict.update(
                    {
                        'vat_%s' % str(tax.get('tag_line_id')[0]): tax.get('vat'),
                        'vat_credit_%s' % str(tax.get('tag_line_id')[0]): tax.get('credit'),
                        'vat_debit_%s' % str(tax.get('tag_line_id')[0]): tax.get('debit')
                    })

        for tax in data.get('tax_lines'):
            if tax.get('tag_tax_ids'):
                new_dict.update(
                    {
                        'net_%s' % str(tax.get('tag_tax_ids')[0]): tax.get('net'),
                        'net_credit_%s' % str(tax.get('tag_tax_ids')[0]): tax.get('credit'),
                        'net_debit_%s' % str(tax.get('tag_tax_ids')[0]): tax.get('debit')
                    })
        return new_dict

    def get_tax_moves(self, date_to, vat_scheme):
        """
        Allows to get the move lines with taxes from the cleint system
        Arguments:
            date_to {Char} -- [date until the routine should get the moves]
            vat_scheme {Char} -- [the type off the VAT scheme wich can be accrual(AC) or cash basis(CB)]
        Returns:
            [dict] -- [dict with all the moves]
        """
        response = self.env['mtd.connection'].open_connection_odoogap().get_payload(vat_scheme)
        channel_id = self.env.ref('hmrc_mtd_client.channel_mtd')

        if response.get('status') == 200:
            account_taxes = self.env['account.tax'].search(
                [
                    ('active', '=', True)
                ])

            if vat_scheme == 'AC':
                params = [0, date_to, self.env.company.id]

            data = {'tax_line': [], 'tax_lines': []}
            for account_tax in account_taxes:
                if vat_scheme == 'AC':
                    params[0] = account_tax.id

                self.env.cr.execute(response.get('message').get('tax_line'), params)
                results = self.env.cr.dictfetchall()
                results[0].update({'tag_line_id': [tag.name for tag in account_tax.tag_ids]})
                data['tax_line'].append(results[0])
                self.env.cr.execute(response.get('message').get('tax_lines'), params)
                results = self.env.cr.dictfetchall()
                results[0].update({'tag_tax_ids': [tag.name for tag in account_tax.tag_ids]})
                data['tax_lines'].append(results[0])

            return self.dict_refactor(data)

        else:
            _logger.error('Response from server :\n status: %s\n message: %s' % (str(response.get('status')), response.get('message')))
            channel_id.message_post('Attempt to run vat calculation failed!\nResponse from server : \nstatus: %s \nmessage: %s' % (
                str(response.get('status')),
                response.get('message')
                )
            )

            return response

    def vat_thread_calculation(self):
        """
            Sends a request to the server within a thread in order to calculate the VAT report for the user
        """
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            channel_id = self.env.ref('hmrc_mtd_client.channel_mtd')

            try:
                submit_data = self.get_tax_moves(self.period.split('-')[1].replace('/', '-'), self.vat_scheme)
                response = self.env['mtd.connection'].open_connection_odoogap().calculate_boxes(submit_data)

                if response.get('status') == 200:
                    channel_id.message_post(
                            body='The VAT calculation was successfull!',
                            message_type="notification"
                        )
                    self.env['mtd.vat.report'].search([('name', '=', self.period.split(':')[1])]).unlink()
                    vat_report_data = {
                            'registration_number': self.env.user.company_id.vat,
                            'vat_scheme': 'Accrual Basis ' if self.vat_scheme == 'AC' else 'Cash Basis',
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
                            'period_key': self.period.split(':')[0]
                        }
                    self.env['mtd.vat.report'].create(vat_report_data)
                else:
                    channel_id.message_post(
                        body='Response from server : \n status: %s\n message: %s' % (str(response.get('status')), response.get('message')),
                        message_type="notification",
                        subtype="mail.mt_comment"
                    )
                new_cr.commit()

            except Exception as ex:
                self._cr.rollback()
                _logger.error('Attempt to run vat calculation failed %s ' % str(ex))
                channel_id.message_post(
                    body='Attempt to run vat calculation failed! %s' % str(ex),
                    message_type="notification"
                )
                new_cr.commit()
                self._cr.close()

    def _sql_get_move_lines_count(self):
        """
            query that gets the number off move that are not submitted
        """

        return """
            SELECT count(account_move.id) FROM account_move
            INNER JOIN account_move_line ON account_move_line.move_id = account_move.id
            INNER JOIN account_move_line_account_tax_rel ON account_move_line.id =
            account_move_line_account_tax_rel.account_move_line_id INNER JOIN
            account_tax ON account_tax.id = account_move_line_account_tax_rel.account_tax_id
            WHERE account_move.state = 'posted'  AND
            account_move.is_mtd_submitted = 'f'  AND
            account_move.company_id in (%s) AND
            account_move.date <= '%s'
        """

    def vat_calculation(self):
        """
        Calculate the vat based on the VAT Formula
        Returns:
            [Dict] -- returns a pop up message
        """
        if self.env.company.submitted_formula:
            self.env.cr.execute(self._sql_get_move_lines_count() % (self.env.user.company_id.id, self.period.split('-')[1].replace('/', '-')))
            results = self.env.cr.dictfetchall()
            view = self.env.ref('hmrc_mtd_client.pop_up_message_view')

            if results[0].get('count') > 0:
                channel_id = self.env.ref('hmrc_mtd_client.channel_mtd')
                channel_id.message_post(
                    body='The VAT calculation has started please check the channel once is completed.',
                    message_type="notification"
                )

                t = threading.Thread(target=self.vat_thread_calculation)
                t.start()

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
                        'default_name': 'The VAT calculation has started please check MTD channel.',
                        'delay': False,
                        'no_delay': True
                    }
                }
            else:
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
                        'default_name': 'There are no invoices available for submission in the given date range.',
                        'delay': True,
                        'no_delay': False
                    }
                }
        else:
            raise UserError('Please submit the VAT formula first.')
