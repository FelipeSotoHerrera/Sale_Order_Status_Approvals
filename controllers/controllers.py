# -*- coding: utf-8 -*-
from odoo import http

# class SaleOrderStatusApprovals(http.Controller):
#     @http.route('/sale_order_status_approvals/sale_order_status_approvals/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sale_order_status_approvals/sale_order_status_approvals/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sale_order_status_approvals.listing', {
#             'root': '/sale_order_status_approvals/sale_order_status_approvals',
#             'objects': http.request.env['sale_order_status_approvals.sale_order_status_approvals'].search([]),
#         })

#     @http.route('/sale_order_status_approvals/sale_order_status_approvals/objects/<model("sale_order_status_approvals.sale_order_status_approvals"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sale_order_status_approvals.object', {
#             'object': obj
#         })