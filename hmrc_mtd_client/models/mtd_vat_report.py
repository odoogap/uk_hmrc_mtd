# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import time
import requests
import json
import datetime

class MtdVatReport(models.Model):
    _name = 'mtd.vat.report'
    _description = 'MTD VAT Report'

    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    registration_number = fields.Char('registration_number')
    vat_scheme = fields.Char('VAT Scheme')
    name = fields.Char('Period Covered')
    period_key = fields.Char('Period Key')
    submission_date = fields.Datetime('Submission Date')
    box_one = fields.Monetary('Box one', currency_field='currency_id')
    vatDueSales = fields.Monetary('Box one result', currency_field='currency_id')
    box_two = fields.Monetary('Box two', currency_field='currency_id')
    vatDueAcquisitions = fields.Monetary('Box two result', currency_field='currency_id')
    box_three = fields.Monetary('Box three', currency_field='currency_id')
    totalVatDue = fields.Monetary('Box three result', currency_field='currency_id')
    box_four = fields.Monetary('Box four', currency_field='currency_id')
    vatReclaimedCurrPeriod = fields.Monetary('Box four result', currency_field='currency_id')
    box_five = fields.Monetary('Box five', currency_field='currency_id')
    netVatDue = fields.Monetary('Box five result', currency_field='currency_id')
    box_six = fields.Monetary('Box six', currency_field='currency_id')
    totalValueSalesExVAT = fields.Monetary('Box six result', currency_field='currency_id')
    box_seven = fields.Monetary('Box seven', currency_field='currency_id')
    totalValuePurchasesExVAT = fields.Monetary('Box seven result', currency_field='currency_id')
    box_eight = fields.Monetary('Box eight', currency_field='currency_id')
    totalValueGoodsSuppliedExVAT = fields.Monetary('Box eight result', currency_field='currency_id')
    box_nine = fields.Monetary('Box nine', currency_field='currency_id')
    totalAcquisitionsExVAT = fields.Monetary('Box nine result', currency_field='currency_id')
    submission_token = fields.Char('Submission token')
    is_submitted = fields.Boolean(defaut=False)
    account_moves = fields.One2many('account.move', 'vat_report_id')
    x_correlation_id = fields.Char('correlation')
    receipt_id = fields.Char('receipt')
    receipt_timestamp = fields.Char('receipt timestamp')
    receipt_signature = fields.Char('receipt signature')
    processing_date = fields.Char('processing date')
    form_bundle_number = fields.Char('form bundle number')
    payment_indicator = fields.Char('payment indicator')
    charge_ref_number = fields.Char('charge reference')

    @api.model
    def create(self, values):
        res = super(MtdVatReport, self).create(values)
        res.write(
            {
                'vatDueSales': round(res.box_one, 2),
                'vatDueAcquisitions': round(res.box_two, 2),
                'totalVatDue': round(res.box_three, 2),
                'vatReclaimedCurrPeriod': round(res.box_four, 2),
                'netVatDue': abs(round(res.box_five, 2)),
                'totalValueSalesExVAT': round(res.box_six, 0),
                'totalValuePurchasesExVAT': round(res.box_seven, 0),
                'totalValueGoodsSuppliedExVAT': round(res.box_eight, 0),
                'totalAcquisitionsExVAT': round(res.box_nine, 0)
            })

        return res

    def sql_get_account_moves(self):
        return """
            SELECT account_move.id
                FROM account_move INNER JOIN account_move_line ON
                account_move.id = account_move_line.move_id
                WHERE account_move_line.move_id=account_move.id AND
                account_move_line.tax_line_id IS NOT NULL AND
                account_move_line.date <= '%s' AND
                account_move.state = 'posted' AND
                account_move.is_mtd_submitted = 'f' AND
                account_move.company_id in (%s)
            UNION
            SELECT account_move.id FROM account_move
                INNER JOIN account_move_line ON account_move_line.move_id = account_move.id
                INNER JOIN account_move_line_account_tax_rel ON account_move_line.id =
                account_move_line_account_tax_rel.account_move_line_id INNER JOIN
                account_tax ON account_tax.id = account_move_line_account_tax_rel.account_tax_id
                WHERE account_move.date <= '%s' AND
                account_move.state = 'posted' AND
                account_move.is_mtd_submitted = 'f' AND
                account_move.company_id in (%s)
        """

    def sql_get_account_move_lines_by_tag(self):
        return """
            SELECT account_move_line.id
                FROM account_move INNER JOIN account_move_line ON
                account_move.id = account_move_line.move_id
                INNER JOIN account_move_line_account_tax_rel ON account_move_line.id =
                account_move_line_account_tax_rel.account_move_line_id INNER JOIN
                account_tax ON account_tax.id = account_move_line_account_tax_rel.account_tax_id
                WHERE account_move.date <= '%s' AND
                account_move.state = 'posted' AND
                account_move.is_mtd_submitted = '%s' %s
                account_move.company_id in (%s) AND
                account_tax.id IN (
                    SELECT account_tax.id
                    FROM account_tax INNER JOIN account_tax_account_tag ON
                    account_tax_account_tag.account_tax_id=account_tax.id INNER JOIN
                    account_account_tag ON account_account_tag.id =
                    account_tax_account_tag.account_account_tag_id
                    WHERE account_account_tag.name IN (%s)
                )
        """

    def get_account_moves(self):
        params = self.env['ir.config_parameter'].sudo()
        taxes = params.get_param('mtd.%s' % self._context.get('taxes').encode("utf-8"), default=False)
        mtd_state = 'f'
        condition = 'AND'

        if not taxes:
            raise UserError('This box does not have any journal entries.')

        if self.is_submitted:
            mtd_state = 't'
            condition = 'AND account_move.vat_report_id in (%s) AND' % self.id

        self.env.cr.execute(self.sql_get_account_move_lines_by_tag() % (
            self.name.split('-')[1],
            mtd_state,
            condition,
            self.env.user.company_id.id,
            str(taxes).strip('[]').encode("utf-8"))
        )
        account_moves = self.env.cr.fetchall()
        view = self.env.ref('account.view_account_journal_tree')
        context = self.env.context.copy()
        list_view = self.env.ref('hmrc_mtd_client.view_move_line_tree').id
        form_view = self.env.ref('account.view_move_line_form').id

        context.update({
            'mtd_date': self.name.split('-')[0].replace('/', '-').strip(),
            'mtd_due_invoice': 1
        })

        action = {
            'name': _(self._context.get('box_name')),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'views': [
                [list_view, 'list'],
                [form_view, 'form']
                ],
            'view_id': view.id,
            'target': 'current',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', [move[0] for move in account_moves])],
            'context': context
        }
        return action

    def check_version(self):
        latest_version = self.env['ir.module.module'].search([('name', '=', 'hmrc_mtd_client')]).latest_version
        values = {
            'odoo_version': 'v10',
            'mtd_client_version': latest_version
        }

        response = self.env['mtd.connection'].open_connection_odoogap().execute('mtd.operations', 'check_version', values)
        if response.get('status') != 200:
            raise UserError(response.get('message'))

    def save_submission_data(self, message, headers):
        self.env['mtd.connection'].sudo().open_connection_odoogap().execute(
            'mtd.operations',
            'validate_submission',
            self.submission_token
        )

        self.write({
                'is_submitted': True,
                'submission_date': datetime.datetime.now(),
                'processing_date': message.get('processingDate'),
                'payment_indicator': message.get('paymentIndicator'),
                'form_bundle_number': message.get('formBundleNumber'),
                'charge_ref_number':message.get('chargeRefNumber'),
                'x_correlation_id': headers.get('X-Correlationid'),
                'receipt_id': headers.get('Receipt-ID'),
                'receipt_timestamp': headers.get('Receipt-Timestamp'),
                'receipt_signature': headers.get('Receipt-Signature')
            })

        self.env.cr.execute(
            self.sql_get_account_moves() % (
            self.name.split('-')[1].replace('/', '-'),
            self.env.user.company_id.id,
            self.name.split('-')[1].replace('/', '-'),
            self.env.user.company_id.id
            )
        )
        results = self.env.cr.fetchall()
        ids = [res[0] for res in results]

        if ids:
            self.env.cr.execute("update account_move set is_mtd_submitted = 't', vat_report_id = %s where id in %s" % (
                self.id,
                str(tuple(ids))
            ))

    @api.multi
    def submit_vat(self):
        self.ensure_one()
        boxes = {
            'vatDueSales': self.vatDueSales,
            'vatDueAcquisitions': self.vatDueAcquisitions,
            'totalVatDue': self.totalVatDue,
            'vatReclaimedCurrPeriod': self.vatReclaimedCurrPeriod,
            'netVatDue': self.netVatDue,
            'totalValueSalesExVAT': self.totalValueSalesExVAT,
            'totalValuePurchasesExVAT': self.totalValuePurchasesExVAT,
            'periodKey': self.period_key,
            'finalised': True,
            'totalValueGoodsSuppliedExVAT': self.totalValueGoodsSuppliedExVAT,
            'totalAcquisitionsExVAT': self.totalAcquisitionsExVAT
        }
        params = self.env['ir.config_parameter'].sudo()
        api_token = params.get_param('mtd.token', default=False)
        hmrc_url = params.get_param('mtd.hmrc.url', default=False)
        token_expire_date = params.get_param('mtd.token_expire_date')

        if float(token_expire_date) - time.time() < 0:
            api_token = self.env['mtd.connection'].refresh_token()

        req_url = '%s/organisations/vat/%s/returns' % (hmrc_url, str(self.env.user.company_id.vrn))
        req_headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/vnd.hmrc.1.0+json',
                'Authorization': 'Bearer %s' % api_token
            }
        response = requests.post(req_url, headers=req_headers, json=boxes)
        self.check_version()
        if response.status_code == 201:
            message = json.loads(response._content.decode("utf-8"))
            headers = response.headers
            view = self.env.ref('hmrc_mtd_client.pop_up_message_view')
            self.save_submission_data(message, headers)

            return {
                'name': 'Success',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'pop.up.message',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': {
                        'default_name': 'Successfully Submitted',
                        'no_delay': False,
                        'delay': True
                    }
                }

        message = json.loads(response._content.decode("utf-8"))
        raise UserError('An error has occurred : \n status: %s \n message: %s' % (
                str(response.status_code), ''.join([error.get('message') for error in message.get('errors')])
            ))
    
    @api.multi
    def verify_submission(self):
        print('verify submission')

        context = self._context.copy()
        context.update({'period_key': self.period_key})
        return self.env['mtd.vat.verification'].with_context(context).verify_submission()
