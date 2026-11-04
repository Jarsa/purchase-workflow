# Copyright 2026 Jarsa, (<https://www.jarsa.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestAccountMoveLineCodeRemove(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.coded_product = cls.env["product.product"].create(
            {
                "name": "Coded Product",
                "type": "service",
                "default_code": "TEST-CODE",
                "description_purchase": "Purchase description",
                "purchase_method": "purchase",
            }
        )
        cls.order = cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "order_line": [
                    Command.create(
                        {
                            "product_id": cls.coded_product.id,
                            "product_qty": 1.0,
                            "price_unit": 100.0,
                        }
                    )
                ],
            }
        )
        cls.order.button_confirm()
        cls.order.action_create_invoice()
        cls.bill = cls.order.invoice_ids
        cls.bill_line = cls.bill.invoice_line_ids

    def test_bill_label_without_default_code(self):
        self.assertEqual(self.bill_line.label, "Coded Product\nPurchase description")

    def test_bill_inverse_label(self):
        self.bill_line.label = "Coded Product\nCustom description"
        self.assertEqual(self.bill_line.name, "Custom description")
        self.assertEqual(self.bill_line.label, "Coded Product\nCustom description")

    def test_bill_label_from_previous_version(self):
        self.bill_line.name = "Coded Product\nPurchase description"
        self.assertEqual(self.bill_line.label, "Coded Product\nPurchase description")

    def test_manual_bill_keeps_default_code(self):
        bill = self._create_invoice(
            move_type="in_invoice",
            partner_id=self.partner_a,
            invoice_line_ids=[Command.create({"product_id": self.coded_product.id})],
        )
        self.assertEqual(
            bill.invoice_line_ids.label,
            "[TEST-CODE] Coded Product\nPurchase description",
        )
