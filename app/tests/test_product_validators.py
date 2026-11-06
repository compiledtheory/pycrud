import unittest

from app.REST.model.products.product_orm import CategoryORM
from app.REST.service.products.product_validators import (
    ValidationError,
    validate_available_quantity,
    validate_price_for_category,
    validate_product_name,
)


class ProductValidatorTests(unittest.TestCase):
    def test_name_accepts_letters_and_digits(self):
        validate_product_name("Laptop42")

    def test_name_requires_length_between_3_and_20(self):
        with self.assertRaises(ValidationError):
            validate_product_name("AB")

    def test_name_rejects_special_characters(self):
        with self.assertRaises(ValidationError):
            validate_product_name("Laptop!")

    def test_price_must_match_category_limits(self):
        category = CategoryORM(name="Furniture", min_price=50.0, max_price=2500.0)
        validate_price_for_category(150.0, category)
        with self.assertRaises(ValidationError):
            validate_price_for_category(10.0, category)

    def test_available_quantity_must_be_non_negative(self):
        validate_available_quantity(0)
        with self.assertRaises(ValidationError):
            validate_available_quantity(-1)


if __name__ == "__main__":
    unittest.main()
