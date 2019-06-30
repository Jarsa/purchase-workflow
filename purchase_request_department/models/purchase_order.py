# Copyright 2019, Jarsa Sistemas, S.A. de C.V.
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _get_my_department(self):
        employees = self.env.user.employee_ids
        return (employees[0].department_id if employees
                else self.env['hr.department'] or False)

    department_id = fields.Many2one('hr.department', 'Department',
                                    default=_get_my_department)

    @api.onchange('user_id')
    def onchange_user_id(self):
        employees = self.user_id.employee_ids
        self.department_id = (employees[0].department_id if employees
                              else self.env['hr.department'] or False)


class ṔurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    department_id = fields.Many2one(comodel_name='hr.department',
                                    related='order_id.department_id',
                                    store=True,
                                    string='Department', readonly=True)
