# -*- coding: utf-8 -*-
{
    'name': "customaddons/advanced_vn_report",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'l10n_lt', 'account', 'sale', 'account_accountant', 'stock_account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/b01_dn_data.xml',
        'data/b02_dn_data.xml',
        'data/b03_dn_data.xml',
        'data/account_journal_data.xml',
        'data/account_move_line_split_contract_sequence.xml',
        'data/transaction_entry_sequence.xml',
        'data/contract_acceptance_sequence.xml',
        'views/templates.xml',
        'views/account_invoice_view.xml',
        'views/account_move_line_split_contract_view.xml',
        'views/sale_order_view.xml',
        'views/account_contract.xml',
        'views/account_asset_inherit_view.xml',
        'views/export_warehouse_tag.xml',
        'views/result_export_warehouse_tag.xml',
        'views/account_move_line_views.xml',
        'views/account_financial_note.xml',
        'views/account_partner_ledger_141.xml',
        'views/transaction_entry_model_view.xml',
        'views/contract_acceptance_view.xml',
        'views/stock_quantity_report_view.xml',
        'wizard/detail_ledger_material_tools_view.xml',
        'wizard/result_detail_ledger_material_tools.xml',
        'wizard/stock_quantity_report_export_view.xml',
        'wizard/stock_quantity_report_file_view.xml',
        'wizard/popup_export_html_finance_report.xml',
        'wizard/popup_test_financial_operation.xml',
        'wizard/warehouse_card_report_export_view.xml',
        'views/account_payment_inherit_view.xml',
        'views/account_payment_report_wizard.xml',
        'views/vn_account_move_line.xml',
        'reports/base_report.xml',
        'reports/action_payment_pdf_export_a5.xml',
        "views/stock_location.xml",
        'views/account_move_inherit_view.xml',
        'views/account_tax_report.xml',
        'views/account_move_report_wizard.xml',
        'views/stock_inventory_view_inherit.xml',
        'reports/action_move_pdf_export_a5.xml',
        'data/cron_job_update_product.xml',
        'views/account_reports_line_template_update.xml',
        'views/revaluation_of_foreign_currency_accounts.xml',
        'views/foreign_currency_revaluation_view.xml',
        'views/asset_sell_form_inherit.xml',
    ],
}
