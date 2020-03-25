from decimal import Decimal
from enum import Enum
from typing import Dict, List

from pydantic import BaseModel

from currency_converter_service.currency import Currency

__all__ = [
    "CurrencyExchangeConvertResponse",
    "CurrencyExchangeRatesLoadRequest",
    "CurrencyExchangeLoadResponse",
    "ExchangeRate",
    "LoadStatus",
]


class CustomModel(BaseModel):
    class Config:
        json_encoders = {Decimal: str}


class CurrencyExchangeConvertResponse(CustomModel):
    from_currency: Currency
    to_currency: Currency
    amount: Decimal
    rate: Decimal
    conversion_result: Decimal
    last_updated: int


class ExchangeRate(CustomModel):
    rate: Decimal
    last_updated: int


class CurrencyExchangeRates(BaseModel):
    base: Currency
    quotes: Dict[Currency, ExchangeRate]


class CurrencyExchangeRatesLoadRequest(BaseModel):
    currency_exchange_rates: List[CurrencyExchangeRates]


class LoadStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class CurrencyExchangeLoadResponse(BaseModel):
    status: LoadStatus
    merge: bool
