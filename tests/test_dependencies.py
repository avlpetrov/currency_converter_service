from typing import Dict, Iterator, Tuple

import pytest

from currency_converter_service.currency import Currency
from currency_converter_service.dependencies import preprocess
from currency_converter_service.models import CurrencyExchangeRatesLoadRequest


@pytest.mark.parametrize(
    "raw_load_request, loadable_exchange_rates",
    [
        (
            CurrencyExchangeRatesLoadRequest(
                **{
                    "currency_exchange_rates": [
                        {
                            "base": "USD",
                            "quotes": {
                                "RUB": {"rate": "79.75", "last_updated": 1584989828}
                            },
                        },
                        {
                            "base": "RUB",
                            "quotes": {
                                "USD": {"rate": "0.013", "last_updated": 1584989897}
                            },
                        },
                    ]
                }
            ),
            (
                (
                    "exchange-rates:USD",
                    {"RUB": '{"rate": "79.75", "last_updated": 1584989828}'},
                ),
                (
                    "exchange-rates:RUB",
                    {"USD": '{"rate": "0.013", "last_updated": 1584989897}'},
                ),
            ),
        ),
        (
            CurrencyExchangeRatesLoadRequest(
                **{
                    "currency_exchange_rates": [
                        {
                            "base": "EUR",
                            "quotes": {
                                "RUB": {"rate": "79.75", "last_updated": 1584989828},
                                "GBP": {"rate": "0.918316", "last_updated": 1584989828},
                                "CHF": {"rate": "1.059278", "last_updated": 1584989828},
                            },
                        },
                    ]
                }
            ),
            (
                (
                    "exchange-rates:EUR",
                    {"RUB": '{"rate": "79.75", "last_updated": 1584989828}'},
                ),
                (
                    "exchange-rates:EUR",
                    {"GBP": '{"rate": "0.918316", "last_updated": 1584989828}'},
                ),
                (
                    "exchange-rates:EUR",
                    {"CHF": '{"rate": "1.059278", "last_updated": 1584989828}'},
                ),
            ),
        ),
    ],
)
def test_preprocess(
    raw_load_request: CurrencyExchangeRatesLoadRequest,
    loadable_exchange_rates: Iterator[Tuple[str, Dict[Currency, str]]],
) -> None:
    assert tuple(preprocess(raw_load_request)) == loadable_exchange_rates
