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

    currency_id = fields.Many2one(
        'res.currency', string='Currency', related='company_id.currency_id')
    company_id = fields.Many2one(
        'res.company', default=lambda self: self.env.user.company_id)
    registration_number = fields.Char('registration_number')
    vat_scheme = fields.Char('VAT Scheme')
    name = fields.Char('Period Covered')
    period_key = fields.Char('Period Key')
    submission_date = fields.Datetime('Submission Date')
    box_one = fields.Monetary('Box one', currency_field='currency_id')
    box_one_adj = fields.Monetary(
        'Box one adjustment', currency_field='currency_id')
    vatDueSales = fields.Monetary(
        'Box one result', currency_field='currency_id')
    box_two = fields.Monetary('Box two', currency_field='currency_id')
    box_two_adj = fields.Monetary(
        'Box two adjustment', currency_field='currency_id')
    vatDueAcquisitions = fields.Monetary(
        'Box two result', currency_field='currency_id')
    box_three = fields.Monetary('Box three', currency_field='currency_id')
    totalVatDue = fields.Monetary(
        'Box three result', currency_field='currency_id')
    box_four = fields.Monetary('Box four', currency_field='currency_id')
    box_four_adj = fields.Monetary(
        'Box four adjustment', currency_field='currency_id')
    vatReclaimedCurrPeriod = fields.Monetary(
        'Box four result', currency_field='currency_id')
    box_five = fields.Monetary('Box five', currency_field='currency_id')
    netVatDue = fields.Monetary(
        'Box five result', currency_field='currency_id')
    box_six = fields.Monetary('Box six', currency_field='currency_id')
    box_six_adj = fields.Monetary(
        'Box six adjustment', currency_field='currency_id')
    totalValueSalesExVAT = fields.Monetary(
        'Box six result', currency_field='currency_id')
    box_seven = fields.Monetary('Box seven', currency_field='currency_id')
    box_seven_adj = fields.Monetary(
        'Box seven adjustment', currency_field='currency_id')
    totalValuePurchasesExVAT = fields.Monetary(
        'Box seven result', currency_field='currency_id')
    box_eight = fields.Monetary('Box eight', currency_field='currency_id')
    box_eight_adj = fields.Monetary(
        'Box eight adjustment', currency_field='currency_id')
    totalValueGoodsSuppliedExVAT = fields.Monetary(
        'Box eight result', currency_field='currency_id')
    box_nine = fields.Monetary('Box nine', currency_field='currency_id')
    box_nine_adj = fields.Monetary(
        'Box nine adjustment', currency_field='currency_id')
    totalAcquisitionsExVAT = fields.Monetary(
        'Box nine result', currency_field='currency_id')
    submission_token = fields.Char('Submission token')
    is_submitted = fields.Boolean(defaut=False)
    account_moves = fields.One2many('account.move', 'vat_report_id')

    @api.model
    def create(self, values):
        res = super(MtdVatReport, self).create(values)
        res.write({'vatDueSales': round(res.box_one + res.box_one_adj, 2), 'vatDueAcquisitions': round(res.box_two + res.box_two_adj, 2),
                   'totalVatDue': round(res.box_three, 2),
                   'vatReclaimedCurrPeriod': round(res.box_four + res.box_four_adj, 2),
                   'netVatDue': abs(round(res.box_five, 2)), 'totalValueSalesExVAT': round(res.box_six + res.box_six_adj, 0),
                   'totalValuePurchasesExVAT': round(res.box_seven + res.box_seven_adj, 0),
                   'totalValueGoodsSuppliedExVAT': round(res.box_eight + res.box_eight_adj, 0),
                   'totalAcquisitionsExVAT': round(res.box_nine + res.box_nine_adj, 0)})
        return res

    @api.multi
    def write(self, values):
        if not self.is_submitted:
            vatDueSales = round((self.box_one + values.get('box_one_adj', self.box_one_adj)), 2)
            vatDueAcquisitions = round((self.box_two + values.get('box_two_adj', self.box_two_adj)), 2)
            totalVatDue = vatDueSales + vatDueAcquisitions
            vatReclaimedCurrPeriod = round((self.box_four + values.get('box_four_adj', self.box_four_adj)), 2)
            netVatDue = round(abs((vatDueSales + vatDueAcquisitions) - vatReclaimedCurrPeriod), 2)

            values.update(
                {'vatDueSales': vatDueSales,
                 'vatDueAcquisitions': vatDueAcquisitions,
                 'totalVatDue': totalVatDue,
                 'vatReclaimedCurrPeriod': vatReclaimedCurrPeriod,
                 'netVatDue': netVatDue,
                 'totalValueSalesExVAT': round((self.box_six + values.get('box_six_adj', self.box_six_adj)), 0),
                 'totalValuePurchasesExVAT': round((self.box_seven + values.get('box_seven_adj', self.box_seven_adj)), 0),
                 'totalValueGoodsSuppliedExVAT': round((self.box_eight + values.get('box_eight_adj', self.box_eight_adj)), 0),
                 'totalAcquisitionsExVAT': round((self.box_nine + values.get('box_nine_adj', self.box_nine_adj)), 0)})
            return super(MtdVatReport, self).write(values)

    @api.onchange('box_one_adj')
    def _onchange_vatDueSales(self):
        self.vatDueSales = self.box_one + self.box_one_adj
        self.totalVatDue = self.vatDueAcquisitions + self.vatDueSales
        self.netVatDue = self.totalVatDue - self.vatReclaimedCurrPeriod

    @api.onchange('box_two_adj')
    def _onchange_vatDueAcquisitions(self):
        self.vatDueAcquisitions = self.box_two + self.box_two_adj
        self.totalVatDue = self.vatDueAcquisitions + self.vatDueSales
        self.netVatDue = self.totalVatDue - self.vatReclaimedCurrPeriod

    @api.onchange('box_four_adj')
    def _onchange_vatReclaimedCurrPeriod(self):
        self.vatReclaimedCurrPeriod = self.box_four + self.box_four_adj
        self.netVatDue = self.totalVatDue - self.vatReclaimedCurrPeriod

    @api.onchange('box_six_adj')
    def _onchange_totalValueSalesExVAT(self):
        self.totalValueSalesExVAT = self.box_six + self.box_six_adj

    @api.onchange('box_seven_adj')
    def _onchange_totalValuePurchasesExVAT(self):
        self.totalValuePurchasesExVAT = self.box_seven + self.box_seven_adj

    @api.onchange('box_eight_adj')
    def _onchange_totalValueGoodsSuppliedExVAT(self):
        self.totalValueGoodsSuppliedExVAT = self.box_eight + self.box_eight_adj

    @api.onchange('box_nine_adj')
    def _onchange_totalAcquisitionsExVAT(self):
        self.totalAcquisitionsExVAT = self.box_nine + self.box_nine_adj

    def sql_select_invoices_by_tag(self):
        return """
            SELECT account_invoice.id FROM account_move
            INNER JOIN account_invoice ON account_invoice.move_id = account_move.id
            INNER JOIN account_move_line ON account_move_line.move_id = account_move.id
            INNER JOIN account_move_line_account_tax_rel ON account_move_line.id =
            account_move_line_account_tax_rel.account_move_line_id INNER JOIN
            account_tax ON account_tax.id = account_move_line_account_tax_rel.account_tax_id INNER JOIN
            account_tax_account_tag ON account_tax_account_tag.account_tax_id =
            account_tax.id INNER JOIN account_account_tag ON
            account_account_tag.id =
            account_tax_account_tag.account_account_tag_id
            WHERE account_move.state = 'posted' AND
            account_move.is_mtd_submitted = 'f' AND
            account_move.date <= '%s'  AND
            account_move.company_id IN ('%s') AND account_account_tag.name in (%s)
        """

    def sql_get_account_move_lines(self):
        return """
            SELECT account_move.id FROM account_move
            INNER JOIN account_move_line ON account_move_line.move_id = account_move.id
            INNER JOIN account_move_line_account_tax_rel ON account_move_line.id =
            account_move_line_account_tax_rel.account_move_line_id INNER JOIN
            account_tax ON account_tax.id = account_move_line_account_tax_rel.account_tax_id
            WHERE account_move.date <= '%s'  AND
            account_move.state = 'posted'  AND
            account_move.is_mtd_submitted = 'f'  AND
            account_move.company_id in (%s)
        """

    @api.multi
    def get_invoices(self):
        for rec in self:
            rec.env.cr.execute(rec.sql_select_invoices_by_tag() % (
                rec.name.split('-')[1], rec.env.user.company_id.id,
                str(rec._context.get('tags')).strip('[]')))
            documents = rec.env.cr.fetchall()
            view = self.env.ref('hmrc_mtd_client.invoice_tree')
            context = self.env.context.copy()

            list_view = self.env.ref('hmrc_mtd_client.invoice_tree').id
            form_view = self.env.ref('account.invoice_form').id
            if self._context.get('tag_type') in ['Box 2', 'Box 4', 'Box 7', 'Box 9']:
                form_view = self.env.ref('account.invoice_supplier_form').id

            context.update(
                {'mtd_date': self.name.split('-')[0].replace('/', '-').strip(), 'mtd_due_invoice': 1})
            action = {'name': _(self._context.get('tag_type')), 'type': 'ir.actions.act_window',
                      'res_model': 'account.invoice', 'views': [[list_view, 'list'], [form_view, 'form']],
                      'view_id': view.id, 'target': 'current', 'view_mode': 'tree,form',
                      'domain': [('id', 'in', [document[0] for document in documents])], 'context': context}
            return action

    @api.multi
    def submit_vat(self):
        self.ensure_one()
        boxes = {'vatDueSales': self.vatDueSales, 'vatDueAcquisitions': self.vatDueAcquisitions,
                    'totalVatDue': self.totalVatDue,
                    'vatReclaimedCurrPeriod': self.vatReclaimedCurrPeriod,
                    'netVatDue': self.netVatDue,
                    'totalValueSalesExVAT': self.totalValueSalesExVAT,
                    'totalValuePurchasesExVAT': self.totalValuePurchasesExVAT, 'periodKey': self.period_key,
                    'finalised': True,
                    'totalValueGoodsSuppliedExVAT': self.totalValueGoodsSuppliedExVAT,
                    'totalAcquisitionsExVAT': self.totalAcquisitionsExVAT}
        params = self.env['ir.config_parameter'].sudo()
        api_token = params.get_param('mtd.token', default=False)
        hmrc_url = params.get_param('mtd.hmrc.url', default=False)
        token_expire_date = params.get_param('mtd.token_expire_date')
        if float(token_expire_date) - time.time() < 0:
            api_token = self.env['mtd.connection'].refresh_token()
        response = requests.post('%s/organisations/vat/%s/returns' % (hmrc_url, str(self.env.user.company_id.vrn)),
                                    headers={'Content-Type': 'application/json',
                                            'Accept': 'application/vnd.hmrc.1.0+json',
                                            'Authorization': 'Bearer %s' % api_token}, json=boxes)

        if response.status_code == 201:
            view = self.env.ref('hmrc_mtd_client.pop_up_message_view')
            self.env['mtd.connection'].sudo().open_connection_odoogap().execute(
                'mtd.operations', 'validate_submission', self.submission_token)
            self.write(
                {'is_submitted': True, 'submission_date': datetime.datetime.now()})
            self.env.cr.execute(self.sql_get_account_move_lines() % (
                self.name.split('-')[1].replace('/', '-'), self.env.user.company_id.id))
            results = self.env.cr.fetchall()
            ids = [res[0] for res in results]
            self.env.cr.execute(
                "update account_move set is_mtd_submitted = 't', vat_report_id = %s where id in %s" % (self.id, str(tuple(ids))))
            self.env.cr.execute(
                "update account_move_line set is_mtd_submitted = 't' where move_id in %s" % str(tuple(ids)))
            return {'name': 'Success', 'type': 'ir.actions.act_window', 'view_type': 'form', 'view_mode': 'form',
                    'res_model': 'pop.up.message', 'views': [(view.id, 'form')], 'view_id': view.id,
                    'target': 'new',
                    'context': {'default_name': 'Successfully Submitted', 'no_delay': False, 'delay': True}}
        message = json.loads(response._content.decode("utf-8"))
        raise UserError(
            'An error has occurred : \n status: %s \n message: %s' % (str(response.status_code), ''.join(
                [error.get('message') for error in message.get('errors')])))
