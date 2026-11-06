import unittest

from app.REST.model.products.product_schema import ProductHistoryEntry
from app.REST.service.products.product_service import list_product_history


class ProductHistoryServiceTests(unittest.TestCase):
    def test_history_entry_schema_has_required_fields(self):
        fields = {"id", "product_id", "action", "previous_state", "current_state", "changed_at"}
        self.assertTrue(fields.issubset(ProductHistoryEntry.model_fields.keys()))

    def test_history_service_function_is_available(self):
        self.assertTrue(callable(list_product_history))


if __name__ == "__main__":
    unittest.main()
