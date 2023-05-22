from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_invoice_reference(self):
        # OVERRIDE
        self.ensure_one()
        vendor_refs = [ref for ref in set(self.line_ids.mapped("purchase_line_id.order_id.name")) if ref]
        if self.ref:
            return [ref for ref in self.ref.split(", ") if ref and ref not in vendor_refs] + vendor_refs
        return vendor_refs

    # Load all unsold PO lines
    @api.onchange("purchase_vendor_bill_id", "purchase_id")
    def _onchange_purchase_auto_complete(self):
        # OVERRIDE
        purchase_vendor_bill = self.purchase_vendor_bill_id.vendor_bill_id
        if purchase_vendor_bill:
            self.invoice_vendor_bill_id = purchase_vendor_bill
            self._onchange_invoice_vendor_bill()
        elif self.purchase_vendor_bill_id.purchase_order_id:
            self.purchase_id = self.purchase_vendor_bill_id.purchase_order_id
        self.purchase_vendor_bill_id = False

        if not self.purchase_id:
            return

        # Copy partner.
        self.partner_id = self.purchase_id.partner_id
        self.fiscal_position_id = self.purchase_id.fiscal_position_id
        self.invoice_payment_term_id = self.purchase_id.payment_term_id
        self.currency_id = self.purchase_id.currency_id
        self.company_id = self.purchase_id.company_id

        # Copy purchase lines.
        po_lines = self.purchase_id.order_line - self.line_ids.mapped("purchase_line_id")
        new_lines = self.env["account.move.line"]
        for line in po_lines.filtered(lambda l: not l.display_type and l.qty_received - l.qty_invoiced > 0):
            new_line = new_lines.new(line._prepare_account_move_line(self))
            new_line.account_id = new_line._get_computed_account()
            new_line._onchange_price_subtotal()
            new_lines += new_line
        new_lines._onchange_mark_recompute_taxes()

        # Compute invoice_origin.
        origins = set(self.line_ids.mapped("purchase_line_id.order_id.name"))
        self.invoice_origin = ",".join(list(origins))

        # Compute ref.
        refs = self._get_invoice_reference()
        self.ref = ", ".join(refs)

        # Compute invoice_payment_ref.
        if len(refs) == 1:
            self.payment_reference = refs[0]

        self.purchase_id = False
        self._onchange_currency()
        bank = self.bank_partner_id.bank_ids and self.bank_partner_id.bank_ids[0]
        self.partner_bank_id = bank
