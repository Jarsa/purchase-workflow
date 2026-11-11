# Copyright 2026 Jarsa, (<https://www.jarsa.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import api, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    # The label of bill lines depends on the display_default_code context, so
    # calling super with that context would cache the value under another key.
    # Lines coming from purchase orders compute it here with the product name only.

    def _get_product_name_without_code(self):
        self.ensure_one()
        return self.product_id.with_context(
            lang=self.move_id._get_lang(), display_default_code=False
        ).display_name

    @api.depends("purchase_line_id")
    def _compute_label(self):
        purchase_lines = self.filtered(
            lambda line: line.product_id and line.purchase_line_id
        )
        res = super(AccountMoveLine, self - purchase_lines)._compute_label()
        for line in purchase_lines:
            product_name = line._get_product_name_without_code()
            if not line.name:
                line.label = product_name
            elif line.name.splitlines()[0] == product_name:
                line.label = line.name
            else:
                line.label = f"{product_name}\n{line.name}"
        return res

    def _inverse_label(self):
        purchase_lines = self.filtered(
            lambda line: line.product_id and line.purchase_line_id and line.label
        )
        res = super(AccountMoveLine, self - purchase_lines)._inverse_label()
        for line in purchase_lines:
            line.name = line.label.removeprefix(
                line._get_product_name_without_code()
            ).removeprefix("\n")
        return res
