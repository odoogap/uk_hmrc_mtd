# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os
import ssl

_logger = logging.getLogger(__name__)

if (not os.environ.get('PYTHONHTTPSVERIFY', '') and
        getattr(ssl, '_create_unverified_context', None)):
    ssl._create_default_https_context = ssl._create_unverified_context


class MtdFuelScaleValues(models.TransientModel):
    _name = 'mtd.fuel.scale'
    _description = "Fuel scale values"

    name = fields.Char(default='Fuel scale value')
    company_currency_id = fields.Many2one('res.currency', readonly=True, default=lambda self: self.env.user.company_id.currency_id)
    vat_fuel_scale_charge = fields.Monetary(currency_field='company_currency_id', required=True)
    vat_period_charge = fields.Monetary(currency_field='company_currency_id', required=True)
    vat_exclusive_period_charge = fields.Monetary(currency_field='company_currency_id', required=True)

    def get_fuel_scale_values(self, date):
        """gets the fuel scale values from server and saves the records
        Returns:
            [dict] -- [fuel scale wizard]
        """
        params = self.env['ir.config_parameter'].sudo()
        submission_period = params.get_param('mtd.submission_period', default=False)

        if not submission_period:
            raise UserError('Please set the submission period.')

        response = self.env['mtd.connection'].open_connection_odoogap().execute(
            'mtd.operations',
            'get_fuel_scale_table',
            submission_period,
            date
        )

        if response.get('status') != 200:
            raise UserError('An error has occurred : \n status: %s \n message: %s' % (
                str(response.get('status')),
                response.get('message')
            ))

        self.search([]).unlink()

        for fuel_charge in response.get('fuel_charges'):
            self.create(
                {
                    'name': fuel_charge.get('CO2_band'),
                    'vat_fuel_scale_charge': fuel_charge.get('vat_fuel_scale_charge'),
                    'vat_period_charge': fuel_charge.get('vat_period_charge'),
                    'vat_exclusive_period_charge': fuel_charge.get('vat_exclusive_period_charge')
                })

        view = self.env.ref('hmrc_mtd_client.fuel_scale_charge_form_wizard')

        return {
                'name': 'Fuel Scale Charge',
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'mtd.fuel.scale.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'context': self._context
            }
