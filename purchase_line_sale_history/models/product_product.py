# Copyright 2026 Jarsa
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from babel.dates import get_month_names

from odoo import fields, models
from odoo.tools.misc import babel_locale_parse, get_lang


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _get_sales_history_pivot(self, date_ref=None):
        """Return the sales history of the product as the widget expects it.

        The shape is the contract of the ``purchase_sales_history`` field
        widget, so any model wanting to show the panel builds its Json value
        from here instead of assembling the pivot again.
        """
        self.ensure_one()
        years_back = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("purchase_line_sale_history.years_back", 2)
        )
        month_names = get_month_names(
            "abbreviated", locale=babel_locale_parse(get_lang(self.env).code)
        )
        date_ref = date_ref or fields.Datetime.now()
        current_year = date_ref.year
        years = [current_year - offset for offset in range(years_back + 1)]
        qty_by_month = self._get_sales_history_quantities(years[-1], current_year)
        data = {}
        for year in years:
            row = []
            for month in range(1, 13):
                qty = qty_by_month.get((year, month))
                if qty is None:
                    # No data at all: a month still to come in the current
                    # year is unknown (None), any other one simply sold zero.
                    is_future = year == current_year and month > date_ref.month
                    row.append(None if is_future else 0)
                else:
                    row.append(round(qty, 2))
            data[str(year)] = row
        return {
            "product_name": self.display_name,
            "years": years,
            "months": [month_names[month] for month in range(1, 13)],
            "data": data,
        }

    def _get_sales_history_quantities(self, year_from, year_to):
        """Return {(year, month): qty} of posted customer invoice quantities
        for the product, with credit notes subtracted."""
        self.ensure_one()
        base_domain = [
            ("product_id", "=", self.id),
            ("parent_state", "=", "posted"),
            ("date", ">=", fields.Date.to_date(f"{year_from}-01-01")),
            ("date", "<=", fields.Date.to_date(f"{year_to}-12-31")),
        ]
        qty_by_month = {}
        for move_type, sign in (("out_invoice", 1), ("out_refund", -1)):
            groups = self.env["account.move.line"]._read_group(
                base_domain + [("move_id.move_type", "=", move_type)],
                groupby=["date:month"],
                aggregates=["quantity:sum"],
            )
            for month_start, qty in groups:
                key = (month_start.year, month_start.month)
                qty_by_month[key] = qty_by_month.get(key, 0.0) + sign * (qty or 0.0)
        return qty_by_month
