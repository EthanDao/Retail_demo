from odoo import fields, models


class ResultExportWarehouseTag(models.TransientModel):
    _name = 'result.export.warehouse.tag'

    file_name = fields.Char()
    file = fields.Binary()
