{
    'name': 'hmrc_mtd_client',
    'version': '1.1.5',
    'summary': 'Client module for management of HMRC',
    'description': """
        Enables the user to commit HMRC VAT return to HMRC api.
    """,
    'category': 'Invoicing Management',
    'author': 'Odoogap',
    'licence': 'LGPL-3',
    'website': 'https://www.odoogap.com/',
    'images': ['images/main_screenshot.png'],
    'depends': [
        'base',
        'account',
        'l10n_uk'
    ],
    'data': [
        'views/vat_sub_view.xml',
        'views/res_config_views.xml',
        'data/mtd_server_config.xml',
        'views/vat_return_view.xml',
        'data/mtd_channel.xml',
        'security/ir.model.access.csv',
        'views/pop_up_message_view.xml',
        'views/mtd_vat_payments_view.xml',
        'views/vat_liabilities_view.xml',
        'views/mtd_fuel_scale_charge_view.xml',
        'views/menu_item_view.xml',
        'views/mtd_formula_views.xml',
        'views/mtd_account_move_line_view.xml',
        'views/mtd_set_old_journal_submission_view.xml'],
    'external_dependencies': {'python': ['odoorpc', 'msgfy']},
    'installable': True,
    'auto_install': False,
    'support': 'info@odoogap.com',
}
