{
    'name': "hmrc_mtd_client",
    'summary': """
        Client module for management of HMRC""",
    'description': """
        Enables the user to commit HMRC VAT return to HMRC api.
    """,
    'author': "Odoogap",
    'website': "https://www.odoomtd.co.uk/",
    'category': 'Invoicing Management',
    'version': '0.1',
    'depends': ['base', 'account', 'l10n_uk'],
    'data': [
        'views/vat_sub_view.xml',
        'views/res_config_views.xml',
        'data/mtd_server_config.xml',
        'views/vat_return_view.xml',
        'data/mtd_channel.xml',
        'views/account_invoice_view.xml',
        'views/pop_up_message_view.xml',
        'views/mtd_vat_payments_view.xml',
        'views/vat_liabilities_view.xml',
        'views/menu_item_view.xml',
        'views/mtd_formula_views.xml'],
    'external_dependencies': {'python': ['odoorpc', 'msgfy']},
}
