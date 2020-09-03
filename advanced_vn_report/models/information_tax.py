from odoo import api, fields, models


class InformationTax(models.Model):
    _name = "information.tax"

    mst = fields.Char(string="Mã số thuế ")  # ct05
    tenNNT = fields.Char(string="Tên Người/Công ty nộp thuế")  # ct04
    dchiNNT = fields.Text(string="Địa chỉ Người/Công ty nộp thuế")  # ct06
    tenHuyenNNT = fields.Char(string="Tên Huyện")  # ct07
    tenTinhNNT = fields.Char(string="Tên Tỉnh/Thành phố")  # ct08
    phone = fields.Char(string="Điện thoại")  # ct09
    fax = fields.Char(string="Số Fax")  # ct10
    email = fields.Char(string="Email")  # ct11
    name_dl_thue = fields.Char(string="Tên đại lý thuế (nếu có)")  # ct12
    mst_dl_thue = fields.Char(string="Mã số thuế")  # ct13
    dchi_dl_thue = fields.Char(string='Địa chỉ')  # ct14
    tenHuyendl_thue = fields.Char(string="Tên Huyện")  # ct15
    tenTinhdl_thue = fields.Char(string="Tên Tỉnh/Thành phố")  # ct16
    phone_dl_thue = fields.Char(string="Điện thoại")  # ct17
    fax_dl_thue = fields.Char(string="Số Fax")  # ct18
    email_dl_thue = fields.Char(string="Email")  # ct19
    days_dl_thue = fields.Integer(string="Hợp đồng đại lý thuế: Số Ngày")  # ct20
