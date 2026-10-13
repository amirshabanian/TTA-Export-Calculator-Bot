"""Basic offline tests for core arithmetic. Run after installing requirements: python -m unittest."""
import unittest
from decimal import Decimal
import bot

class CalculationTests(unittest.TestCase):
    def test_persian_digits(self):
        self.assertEqual(bot.to_decimal("۱۲۳٬۴۵۶٫۷۸"), Decimal("123456.78"))

    def test_gross_weight_and_rounding(self):
        data = {
            "packages": "100", "gross_kg": "10", "net_kg": "9",
            "product_price": "100000", "pack_labor": "5000", "profit": "10000",
            "land": "1000000", "clearance": "500000", "sea_usd": "1000",
            "fx": "100000", "tehran_tax_pct": "3", "uae_aed_rate": "3.685",
            "switch_bill_usd": "0", "cross_stuffing_usd": "0", "sea_payment_method": "tehran",
        }
        result = bot.calculate(data)
        self.assertEqual(result["total_gross"], Decimal("1000"))
        self.assertEqual(result["total_net"], Decimal("900"))
        self.assertEqual(result["customer_price"] % Decimal("0.05"), Decimal("0.00"))
        self.assertGreaterEqual(result["customer_price"], result["cost_usd_kg"])

    def test_reject_net_weight_above_gross(self):
        data = {
            "packages": "1", "gross_kg": "5", "net_kg": "6",
            "product_price": "1", "pack_labor": "0", "profit": "0",
            "land": "0", "clearance": "0", "sea_usd": "0", "fx": "1",
        }
        with self.assertRaises(ValueError):
            bot.calculate(data)

if __name__ == "__main__":
    unittest.main()
