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
    # update Sale taxes tags
    env.ref('l10n_uk.1_ST0').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st0').id})
    env.ref('l10n_uk.1_ST2').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st2').id})
    env.ref('l10n_uk.1_ST4').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st4').id})
    env.ref('l10n_uk.1_ST5').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st5').id})
    env.ref('l10n_uk.1_ST11').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_st11').id})

    # update Purchase taxes tags
    env.ref('l10n_uk.1_PT0').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt0').id})
    env.ref('l10n_uk.1_PT2').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt2').id})
    env.ref('l10n_uk.1_PT5').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt5').id})
    env.ref('l10n_uk.1_PT7').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt7').id})
    env.ref('l10n_uk.1_PT8').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt8').id})
    env.ref('l10n_uk.1_PT11').write({'tag_ids': env.ref('hmrc_mtd_client.mtd_tag_pt11').id})