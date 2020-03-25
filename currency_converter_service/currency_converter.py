from decimal import Decimal


def calculate_conversion(amount: Decimal, rate: Decimal) -> Decimal:
    conversion_result = amount * rate

    return conversion_result
