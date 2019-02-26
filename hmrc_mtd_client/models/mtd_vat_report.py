# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
import time
import requests
import json
import datetime


class MtdVatReport(models.Model):
    _name = 'mtd.vat.report'

    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)
    registration_number = fields.Char('registration_number')
    vat_scheme = fields.Char('VAT Scheme')
    name = fields.Char('Period Covered')
    period_key = fields.Char('Period Key')
    submission_date = fields.Datetime('Submission Date')
    box_one = fields.Monetary('Box one', currency_field='currency_id')
    box_one_adj = fields.Monetary('Box one adjustment', currency_field='currency_id')
    vatDueSales = fields.Monetary('Box one result', currency_field='currency_id')
    box_two = fields.Monetary('Box two', currency_field='currency_id')
    box_two_adj = fields.Monetary('Box two adjustment', currency_field='currency_id')
    vatDueAcquisitions = fields.Monetary('Box two result', currency_field='currency_id')
    box_three = fields.Monetary('Box three', currency_field='currency_id')
    box_three_adj = fields.Monetary('Box three adjustment', currency_field='currency_id')
    totalVatDue = fields.Monetary('Box three result', currency_field='currency_id')
    box_four = fields.Monetary('Box four', currency_field='currency_id')
    box_four_adj = fields.Monetary('Box four adjustment', currency_field='currency_id')
    vatReclaimedCurrPeriod = fields.Monetary('Box four result', currency_field='currency_id')
    box_five = fields.Monetary('Box five', currency_field='currency_id')
    box_five_adj = fields.Monetary('Box five adjustment', currency_field='currency_id')
    netVatDue = fields.Monetary('Box five result', currency_field='currency_id')
    box_six = fields.Monetary('Box six', currency_field='currency_id')
    box_six_adj = fields.Monetary('Box six adjustment', currency_field='currency_id')
    totalValueSalesExVAT = fields.Monetary('Box six result', currency_field='currency_id')
    box_seven = fields.Monetary('Box seven', currency_field='currency_id')
    box_seven_adj = fields.Monetary('Box seven adjustment', currency_field='currency_id')
    totalValuePurchasesExVAT = fields.Monetary('Box seven result', currency_field='currency_id')
    box_eight = fields.Monetary('Box eight', currency_field='currency_id')
    box_eight_adj = fields.Monetary('Box eight adjustment', currency_field='currency_id')
    totalValueGoodsSuppliedExVAT = fields.Monetary('Box eight result', currency_field='currency_id')
    box_nine = fields.Monetary('Box nine', currency_field='currency_id')
    box_nine_adj = fields.Monetary('Box nine adjustment', currency_field='currency_id')
    totalAcquisitionsExVAT = fields.Monetary('Box nine result', currency_field='currency_id')
    submission_token = fields.Char('Submission token')
    is_submitted = fields.Boolean(defaut=False)

    @api.model
    def create(self, values):
        res = super(MtdVatReport, self).create(values)
        res.write({'vatDueSales': res.box_one + res.box_one_adj, 'vatDueAcquisitions': res.box_two + res.box_two_adj,
                   'totalVatDue': res.box_three + res.box_three_adj,
                   'vatReclaimedCurrPeriod': res.box_four + res.box_four_adj,
                   'netVatDue': res.box_five + res.box_five_adj, 'totalValueSalesExVAT': res.box_six + res.box_six_adj,
                   'totalValuePurchasesExVAT': res.box_seven + res.box_seven_adj,
                   'totalValueGoodsSuppliedExVAT': res.box_eight + res.box_eight_adj,
                   'totalAcquisitionsExVAT': res.box_nine + res.box_nine_adj})
        return res

    @api.multi
    def write(self, values):
        if not self.is_submitted:
            values.update(
                {'vatDueSales': self.box_one + values.get('box_one_adj', self.box_one_adj),
                 'vatDueAcquisitions': self.box_two + values.get('box_two_adj', self.box_two_adj),
                 'totalVatDue': self.box_three + values.get('box_three_adj', self.box_three_adj),
                 'vatReclaimedCurrPeriod': self.box_four + values.get('box_four_adj', self.box_four_adj),
                 'netVatDue': self.box_five + values.get('box_five_adj', self.box_five_adj),
                 'totalValueSalesExVAT': self.box_six + values.get('box_six_adj', self.box_six_adj),
                 'totalValuePurchasesExVAT': self.box_seven + values.get('box_seven_adj', self.box_seven_adj),
                 'totalValueGoodsSuppliedExVAT': self.box_eight + values.get('box_eight', self.box_eight_adj),
                 'totalAcquisitionsExVAT': self.box_nine + values.get('box_nine_adj', self.box_nine_adj)})
            return super(MtdVatReport, self).write(values)

    @api.onchange('box_one_adj')
    def _onchange_vatDueSales(self):
        self.vatDueSales = self.box_one + self.box_one_adj

    @api.onchange('box_two_adj')
    def _onchange_vatDueAcquisitions(self):
        self.vatDueAcquisitions = self.box_two + self.box_two_adj

    @api.onchange('box_three_adj')
    def _onchange_totalVatDue(self):
        self.totalVatDue = self.box_three + self.box_three_adj

    @api.onchange('box_four_adj')
    def _onchange_vatReclaimedCurrPeriod(self):
        self.vatReclaimedCurrPeriod = self.box_four + self.box_four_adj

    @api.onchange('box_five_adj')
    def _onchange_netVatDue(self):
        self.netVatDue = self.box_five + self.box_five_adj

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
            account_move.date <= '%s'  AND
            account_move.company_id IN ('%s') AND account_account_tag.name in (%s)
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
        for rec in self:
            boxes = {'vatDueSales': round(rec.vatDueSales, 2), 'vatDueAcquisitions': round(rec.vatDueAcquisitions, 2),
                     'totalVatDue': round(rec.totalVatDue, 2),
                     'vatReclaimedCurrPeriod': round(rec.vatReclaimedCurrPeriod, 2),
                     'netVatDue': abs(round(rec.netVatDue, 2)),
                     'totalValueSalesExVAT': round(rec.totalValueSalesExVAT, 0),
                     'totalValuePurchasesExVAT': round(rec.totalValuePurchasesExVAT, 0), 'periodKey': rec.period_key,
                     'finalised': True,
                     'totalValueGoodsSuppliedExVAT': round(rec.totalValueGoodsSuppliedExVAT, 0),
                     'totalAcquisitionsExVAT': round(rec.totalAcquisitionsExVAT, 0)}
            params = rec.env['ir.config_parameter'].sudo()
            api_token = params.get_param('mtd.token', default=False)
            hmrc_url = params.get_param('mtd.hmrc.url', default=False)
            token_expire_date = params.get_param('mtd.token_expire_date')
            if float(token_expire_date) - time.time() < 0:
                api_token = rec.env['mtd.connection'].refresh_token()
            response = requests.post('%s/organisations/vat/%s/returns' % (hmrc_url, str(rec.env.user.company_id.vrn)),
                                     headers={'Content-Type': 'application/json',
                                              'Accept': 'application/vnd.hmrc.1.0+json',
                                              'Authorization': 'Bearer %s' % api_token}, json=boxes)

            if response.status_code == 201:
                view = rec.env.ref('hmrc_mtd_client.pop_up_message_view')
                rec.env['mtd.connection'].sudo().open_connection_odoogap().execute(
                    'mtd.operations', 'validate_submission', rec.submission_token)
                rec.write({'is_submitted': True, 'submission_date': datetime.datetime.now()})
                rec.env.cr.execute(
                    "update account_move set is_mtd_submitted = 't' where date <= '%s'" % (rec.name.split('-')[1]))
                return {'name': 'Success', 'type': 'ir.actions.act_window', 'view_type': 'form', 'view_mode': 'form',
                        'res_model': 'pop.up.message', 'views': [(view.id, 'form')], 'view_id': view.id,
                        'target': 'new',
                        'context': {'default_name': 'Successfully Submitted', 'no_delay': False, 'delay': True}}
            message = json.loads(response._content.decode("utf-8"))
            raise UserError(
                'An error has occurred : \n status: %s \n message: %s' % (str(response.status_code), ''.join(
                    [error.get('message') for error in message.get('errors')])))
