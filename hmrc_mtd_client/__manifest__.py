{
    'name': 'HMRC - MTD',
    'version': '1.1.13',
    'summary': 'Client module for management of HMRC',
    'description': """
        Enables the user to commit HMRC VAT return to HMRC api.
    """,
    'category': 'Invoicing Management',
    'author': 'ERPGAP',
    'licence': 'LGPL-3',
    'website': 'https://www.erpgap.com/',
    'images': ['images/main_screenshot.png'],
    'depends': [
        'base',
        'account',
        'l10n_uk'
    ],
    'data': [
        'views/res_config_views.xml',
        'views/pop_up_message_views.xml',
        'views/mtd_set_old_journal_submission_views.xml',
        'views/vat_sub_views.xml',
        'views/vat_return_views.xml',
        'views/menu_item_views.xml',
        'views/mtd_formula_views.xml',
        'views/account_views.xml',
        'data/mtd_channel.xml',
        'data/mtd_cron_data.xml',
        'data/mtd_server_config.xml',
        'data/mtd_taxes_tags.xml',
        'data/mtd_uk_taxes.xml',
        'views/templates.xml',
        'security/ir.model.access.csv'
    ],
    'external_dependencies': {'python': ['odoorpc', 'msgfy', 'odoogap-mtd', 'odoo-client-lib']},
    'installable': True,
    'auto_install': False,
    'support': 'info@erpgap.com',
    'post_init_hook': '_synchronize_taxes_tags'
}
