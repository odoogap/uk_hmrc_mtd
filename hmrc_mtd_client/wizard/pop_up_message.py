# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import api, fields, models, _
import time


class pop_up_message(models.TransientModel):
    _name = "pop.up.message"
    _description="pop up message"

    def get_message(self):
        return self.env.context.get("message")

    name = fields.Text(string="Message", readonly=True, default=get_message)

    def validate_pop_up(self):
        time.sleep(5)
        return {
            'name': _('VAT Reports'),
            'type': 'ir.actions.act_window',
            'res_model': 'mtd.vat.report',
            'view_mode': 'tree,form',
            'view_type': 'tree',
            'views': [
                [self.env.ref('hmrc_mtd_client.mtd_vat_report_tree_view').id, 'list'],
                [self.env.ref('hmrc_mtd_client.mtd_vat_report_form').id, 'form']
            ],
            'context': {"search_default_not_submitted": 1}
        }
