# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools.safe_eval import safe_eval
import os
import ssl
import msgfy
import odoorpc

class MtdSetOldJournalSubmission(models.TransientModel):
    _name = 'mtd.set.old.journal.submission'
    _description = 'allows the user to update submission state of old journals'

    init_submission_date = fields.Date(string="Init submission date")

    @api.multi
    def set_init_submission_date(self):
        self.ensure_one()
        view = self.env.ref('hmrc_mtd_client.pop_up_message_view')
        self.env.cr.execute(
            """
                UPDATE account_move 
                SET is_mtd_submitted = 't'
                WHERE date < '%s' AND account_move.company_id IN (%s)
                AND account_move.state='posted'
            """ % (
            self.init_submission_date,
            self.env.user.company_id.id
        ))
        self.env.cr.execute(
            """
                UPDATE account_move 
                SET is_mtd_submitted = 'f'
                WHERE date >= '%s' AND account_move.company_id IN (%s)
                AND account_move.state='posted'
            """ % (
            self.init_submission_date,
            self.env.user.company_id.id
        ))

        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('mtd.is_set_old_journal', True)

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
                    'default_name': 'The date has been sucessfully set.',
                    'no_delay': False,
                    'delay': True
                }
            }