from odoo import fields, models, api

class StockQuantity_reportFile (models.TransientModel):
    _name = 'stock.quantity.report.file'
    file_name = fields.Char()
    file = fields.Binary()
    


