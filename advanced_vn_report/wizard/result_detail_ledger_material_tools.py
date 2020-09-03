from odoo import fields, models, api


class ResultDetailLedgerMaterialTools (models.TransientModel):
    _name = 'result.detail.ledger.material.tools'
    file_name = fields.Char()
    file = fields.Binary(string='Tài liệu')



