# Copyright 2026 Jarsa, (<https://www.jarsa.com>)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo.fields import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPurchaseProductCodeRemove(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.coded_product, cls.no_description_product = cls.env[
            "product.product"
        ].create(
            [
                {
                    "name": "Coded Product",
                    "default_code": "TEST-CODE",
                    "description_purchase": "Purchase description",
                },
                {"name": "No Description Product", "default_code": "TEST-NODESC"},
            ]
        )
        cls.order = cls._create_po(cls.coded_product)
        cls.line = cls.order.order_line

    @classmethod
    def _create_po(cls, product):
        return cls.env["purchase.order"].create(
            {
                "partner_id": cls.partner_a.id,
                "order_line": [
                    Command.create({"product_id": product.id, "product_qty": 1.0})
                ],
            }
        )

    def test_label_without_default_code(self):
        self.assertEqual(self.line.name, "Purchase description")
        self.assertEqual(self.line.label, "Coded Product\nPurchase description")

    def test_label_without_description(self):
        line = self._create_po(self.no_description_product).order_line
        self.assertEqual(line.label, "No Description Product")

    def test_inverse_label(self):
        self.line.label = "Coded Product\nCustom description"
        self.assertEqual(self.line.name, "Custom description")
        self.assertEqual(self.line.label, "Coded Product\nCustom description")

    def test_label_from_previous_version(self):
        # Lines created before 18.0 already hold the product name, without
        # the code, at the beginning of their description.
        self.line.name = "Coded Product\nPurchase description"
        self.assertEqual(self.line.label, "Coded Product\nPurchase description")

    def test_vendor_product_code_kept(self):
        # Only the internal reference is removed, the vendor product code is
        # still shown so the vendor can identify the product.
        self.coded_product.seller_ids = [
            Command.create(
                {
                    "partner_id": self.partner_a.id,
                    "product_code": "VENDOR-CODE",
                    "price": 10.0,
                }
            )
        ]
        line = self._create_po(self.coded_product).order_line
        self.assertEqual(
            line.label, "[VENDOR-CODE] Coded Product\nPurchase description"
        )

    def test_report_without_default_code(self):
        for report in (
            "purchase.report_purchase_quotation",
            "purchase.action_report_purchase_order",
        ):
            html = self.env["ir.actions.report"]._render_qweb_html(
                report, self.order.ids
            )[0]
            self.assertIn(b"Coded Product", html)
            self.assertNotIn(b"TEST-CODE", html)
