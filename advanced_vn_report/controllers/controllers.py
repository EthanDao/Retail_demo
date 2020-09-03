# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape, datetime

import json


class FinancialReportController(http.Controller):

    @http.route('/advanced/account_reports', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report(self, model, options, output_format, token, financial_id=None, **kw):
        uid = request.session.uid
        account_report_model = request.env['account.report']
        options = json.loads(options)
        cids = request.httprequest.cookies.get('cids', str(request.env.user.company_id.id))
        allowed_company_ids = [int(cid) for cid in cids.split(',')]
        report_obj = request.env[model].with_user(uid).with_context(allowed_company_ids=allowed_company_ids)
        if financial_id and financial_id != 'null':
            report_obj = report_obj.browse(int(financial_id))
        report_name = report_obj.get_report_filename(options)
        try:
            response = None
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', account_report_model.get_export_mime_type('xlsx')),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                response.stream.write(report_obj.advanced_get_xlsx(options))
            response.set_cookie('fileToken', token)
            return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))

class PdfReportController(http.Controller):

    @http.route('/report/pdf/account.payment/', type='http', auth="user")
    def report_pdf_account_payment(self):
        latest_account_payment_pdf_wizard = request.env['account.payment.pdf.wizard'].sudo().search(
            [('create_uid', '=', request.uid)], limit=1, order='id desc')
        pdf = request.env.ref('advanced_vn_report.action_payment_pdf_export_a5').sudo().render_qweb_pdf(
            [latest_account_payment_pdf_wizard.account_payment_id.id])[0]
        file_name = 'Phieu_thu_chi_' + datetime.now().strftime("%Y%m%d%H%M%S")
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'inline; filename=' + file_name + '.pdf')
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)

    @http.route('/report/pdf/account.move/', type='http', auth="user")
    def report_pdf_account_move(self):
        latest_account_move_pdf_wizard = request.env['account.move.pdf.wizard'].sudo().search(
            [('create_uid', '=', request.uid)], limit=1, order='id desc')
        pdf = request.env.ref('advanced_vn_report.action_move_pdf_export_a5').sudo().render_qweb_pdf(
            [latest_account_move_pdf_wizard.account_move_id.id])[0]
        file_name = 'Phieu_thu_chi_' + datetime.now().strftime("%Y%m%d%H%M%S")
        pdfhttpheaders = [
            ('Content-Type', 'application/pdf'),
            ('Content-Length', len(pdf)),
            ('Content-Disposition', 'inline; filename=' + file_name + '.pdf')
        ]
        return request.make_response(pdf, headers=pdfhttpheaders)
