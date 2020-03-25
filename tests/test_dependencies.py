from operator import eq, ne
from typing import Callable, Dict, Iterable, Iterator, Tuple

import pytest
from aioredis import Redis
from more_itertools import first

from currency_converter_service.currency import Currency
from currency_converter_service.dependencies import (
    CurrencyExchangeRatesStorage,
    preprocess,
)
from currency_converter_service.dependencies.rates_storage import LoadableExchangeRates
from currency_converter_service.models import (
    CurrencyExchangeRatesLoadRequest,
    ExchangeRate,
    LoadStatus,
)


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


@pytest.mark.parametrize(
    # fmt: off
    (
        "base_currency, quote_currency, "
        "base_currency_storage_key, "
        "stored_exchange_rates, "
        "expected_exchange_rate"
    ),
    [
        (
            Currency.EUR, Currency.GBP,
            "exchange-rates:EUR",
            {
                "RUB": '{"rate": "79.75", "last_updated": 1584989828}',
                "GBP": '{"rate": "0.918316", "last_updated": 1584989828}',
            },
            ExchangeRate(rate="0.918316", last_updated=1584989828),
        ),
        (
            Currency.EUR, Currency.GBP,
            "exchange-rates:RUB",
            {"RUB": '{"rate": "79.75", "last_updated": 1584989828}'},
            None,
        ),
        (
            Currency.EUR, Currency.GBP,
            "exchange-rates:RUB", {},
            None,
        ),
    ],
    # fmt: on
)
@pytest.mark.asyncio
async def test_fetch_exchange_rate(
    database: Redis,
    base_currency: Currency,
    quote_currency: Currency,
    base_currency_storage_key: str,
    stored_exchange_rates: Tuple[str, Dict[Currency, str]],
    expected_exchange_rate: ExchangeRate,
) -> None:
    if stored_exchange_rates:
        await database.hmset_dict(base_currency_storage_key, stored_exchange_rates)

    currency_exchange_rates_storage = CurrencyExchangeRatesStorage(database)
    fetched_exchange_rate = await currency_exchange_rates_storage.fetch_exchange_rate(
        base_currency, quote_currency
    )

    assert fetched_exchange_rate == expected_exchange_rate


@pytest.mark.parametrize(
    (
        "loadable_exchange_rates, "
        "merge, "
        "base_currency_storage_key, "
        "preloaded_exchange_rates, "
        "stored_exchange_ratesafter_load, "
        "operator ,"
        "expected_load_status"
    ),
    [
        (
            (
                (
                    "exchange-rates:EUR",
                    {
                        "RUB": '{"rate": "79.75", "last_updated": 1584989828}',
                        "CHF": '{"rate": "1.059278", "last_updated": 1584989828}',
                    },
                ),
            ),
            False,
            "exchange-rates:EUR",
            {"GBP": '{"rate": "0.918316", "last_updated": 1584989828}'},
            {
                "RUB": '{"rate": "79.75", "last_updated": 1584989828}',
                "CHF": '{"rate": "1.059278", "last_updated": 1584989828}',
            },
            eq,
            LoadStatus.SUCCESS,
        ),
        (
            (
                (
                    "exchange-rates:EUR",
                    {
                        "RUB": '{"rate": "79.75", "last_updated": 1584989828}',
                        "CHF": '{"rate": "1.059278", "last_updated": 1584989828}',
                    },
                ),
            ),
            True,
            "exchange-rates:EUR",
            {"GBP": '{"rate": "0.918316", "last_updated": 1584989828}'},
            {
                "RUB": '{"rate": "79.75", "last_updated": 1584989828}',
                "CHF": '{"rate": "1.059278", "last_updated": 1584989828}',
            },
            ne,
            LoadStatus.SUCCESS,
        ),
    ],
)
@pytest.mark.asyncio
async def test_load_exchange_rates_succeeded(
    database: Redis,
    loadable_exchange_rates: Iterable[LoadableExchangeRates],
    merge: bool,
    base_currency_storage_key,
    preloaded_exchange_rates: Tuple[str, Dict[Currency, str]],
    stored_exchange_ratesafter_load: Tuple[str, Dict[Currency, str]],
    operator: Callable,
    expected_load_status: LoadStatus,
) -> None:
    if preloaded_exchange_rates:
        await database.hmset_dict(base_currency_storage_key, preloaded_exchange_rates)

    _, exchange_rates = first(loadable_exchange_rates)

    currency_exchange_rates_storage = CurrencyExchangeRatesStorage(database)
    status = await currency_exchange_rates_storage.load_exchange_rates(
        loadable_exchange_rates, merge
    )

    exchange_rates_after_load = await database.hgetall(base_currency_storage_key)
    assert operator(exchange_rates, exchange_rates_after_load)

    assert status == expected_load_status
