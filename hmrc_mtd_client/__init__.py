# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import wizard

from odoo.api import Environment, SUPERUSER_ID


def _synchronize_taxes_tags(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {'active_test': False})
    '''
        This function updates the tags for all the default l10n_uk taxes when the module is installed.
        This tags will be used on the taxes on the formula, during the taxes calculation for MTD
    '''
    for company in env['res.company'].search([('country_id', '=', env.ref('base.uk'))]):
        # update Sale taxes tags
        env.ref(f'l10n_uk.{company.id}_ST0').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st0').id})
        env.ref(f'l10n_uk.{company.id}_ST2').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st2').id})
        env.ref(f'l10n_uk.{company.id}_ST4').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st4').id})
        env.ref(f'l10n_uk.{company.id}_ST5').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st5').id})
        env.ref(f'l10n_uk.{company.id}_ST11').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st11').id})

        # update Purchase taxes tags
        env.ref(f'l10n_uk.{company.id}_PT0').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt0').id})
        env.ref(f'l10n_uk.{company.id}_PT2').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt2').id})
        env.ref(f'l10n_uk.{company.id}_PT5').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt5').id})
        env.ref(f'l10n_uk.{company.id}_PT7').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt7').id})
        env.ref(f'l10n_uk.{company.id}_PT8').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt8').id})
        env.ref(f'l10n_uk.{company.id}_PT11').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt11').id})
