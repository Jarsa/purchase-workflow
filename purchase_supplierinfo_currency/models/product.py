# Copyright 2019 Jarsa Sistemas S.A. de C.V.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def _select_seller(
            self, partner_id=False, quantity=0.0, date=None, uom_id=False):
        self.ensure_one()
        if date is None:
            date = fields.Date.context_today(self)
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        currency_id = self._context.get('currency_id')
        sellers = self.seller_ids
        if currency_id:
            sellers = sellers.with_context(currency_id=currency_id).filtered(
                lambda s: s.currency_id.id == currency_id)
        res = self.env['product.supplierinfo']
        for seller in sellers:
            # Set quantity in UoM of seller
            quantity_uom_seller = quantity
            if quantity_uom_seller and uom_id and uom_id != seller.product_uom:
                quantity_uom_seller = uom_id._compute_quantity(
                    quantity_uom_seller, seller.product_uom)
            if seller.date_start and seller.date_start > date:
                continue
            if seller.date_end and seller.date_end < date:
                continue
            if partner_id and seller.name not in [
                    partner_id, partner_id.parent_id]:
                continue
            if float_compare(
                    quantity_uom_seller, seller.min_qty,
                    precision_digits=precision) == -1:
                continue
            if seller.product_id and seller.product_id != self:
                continue
            res |= seller
            break
        return res
