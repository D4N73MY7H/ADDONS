# -*- coding: utf-8 -*-
# from odoo import http


# class Local/commprog/crmCp(http.Controller):
#     @http.route('/local/commprog/crm_cp/local/commprog/crm_cp', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/local/commprog/crm_cp/local/commprog/crm_cp/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('local/commprog/crm_cp.listing', {
#             'root': '/local/commprog/crm_cp/local/commprog/crm_cp',
#             'objects': http.request.env['local/commprog/crm_cp.local/commprog/crm_cp'].search([]),
#         })

#     @http.route('/local/commprog/crm_cp/local/commprog/crm_cp/objects/<model("local/commprog/crm_cp.local/commprog/crm_cp"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('local/commprog/crm_cp.object', {
#             'object': obj
#         })
