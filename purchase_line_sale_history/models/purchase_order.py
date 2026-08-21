# Copyright 2026 Jarsa
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    sales_history_line_id = fields.Many2one(
        comodel_name="purchase.order.line",
        string="Sales History Line",
        copy=False,
        help="Order line whose product sales history is displayed.",
    )
    sales_history_data = fields.Json(
        compute="_compute_sales_history_data",
        export_string_translation=False,
    )

    @api.onchange("order_line")
    def _onchange_order_line_sales_history(self):
        # Line-level onchanges cannot reach sibling lines, so the live
        # exclusivity is handled here. sales_history_line_id round-trips
        # through the client between onchange calls, so it reliably tells
        # which line was active before this change, even before saving.
        active = self.order_line.filtered("show_sales_history")
        prev = self.sales_history_line_id
        # In the onchange environment the lines are NewId records while the
        # many2one holds the real id, so compare through _origin.
        new = (
            active.filtered(lambda line: prev not in (line, line._origin))[-1:]
            or active[:1]
        )
        (active - new).show_sales_history = False
        self.sales_history_line_id = new

    @api.depends("sales_history_line_id.product_id", "date_order")
    def _compute_sales_history_data(self):
        for order in self:
            product = order.sales_history_line_id.product_id
            order.sales_history_data = (
                product._get_sales_history_pivot(order.date_order)
                if product
                else False
            )
