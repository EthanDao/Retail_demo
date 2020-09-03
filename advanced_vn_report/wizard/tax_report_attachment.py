from odoo import api, fields, models


class TaxReportAttachment(models.TransientModel):
    _name = "tax.report.attachment"

    file = fields.Binary(string="File")
    file_name = fields.Char(string="Tên file")
