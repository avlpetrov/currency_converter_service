import json
from typing import Dict, Iterable, Iterator, Optional, Tuple

from aioredis import Redis
from fastapi.encoders import jsonable_encoder

from currency_converter_service.currency import Currency
from currency_converter_service.models import (
    CurrencyExchangeRatesLoadRequest,
    ExchangeRate,
    LoadStatus,
)

LoadableExchangeRates = Tuple[str, Dict[Currency, str]]


class CurrencyExchangeRatesStorage:
    def __init__(self, connection_pool: Redis) -> None:
        self._connection_pool = connection_pool

    async def fetch_exchange_rate(
        self, base_currency: Currency, quote_currency: Currency
    ) -> Optional[ExchangeRate]:
        base_currency_storage_key = as_storage_key(base_currency)
        serialized_rate = await self._connection_pool.hget(
            base_currency_storage_key, quote_currency.value
        )

        currency_exchange_rate = None
        if serialized_rate:
            deserialized_rate = json.loads(serialized_rate)
            currency_exchange_rate = ExchangeRate(
                rate=deserialized_rate["rate"],
                last_updated=deserialized_rate["last_updated"],
            )

        return currency_exchange_rate

    async def load_exchange_rates(
        self, loadable_exchange_rates: Iterable[LoadableExchangeRates], merge: bool
    ) -> LoadStatus:
        transaction = self._connection_pool.multi_exec()
        if merge is False:
            transaction.flushdb()

        for base_currency_key, quote_to_rate in loadable_exchange_rates:
            transaction.hmset_dict(base_currency_key, quote_to_rate)

        results = await transaction.execute(return_exceptions=True)
        succeeded = all(not isinstance(result, Exception) for result in results)

        return LoadStatus.SUCCESS if succeeded else LoadStatus.FAILURE


def as_storage_key(currency: Currency) -> str:
    storage_key = f"exchange-rates:{currency.value}"
    return storage_key


def preprocess(
    request: CurrencyExchangeRatesLoadRequest,
) -> Iterator[LoadableExchangeRates]:
    """Preprocess currency exchange rates to make it loadable to storage."""
    for currency_exchange_rates in request.currency_exchange_rates:
        base_currency_storage_key = as_storage_key(currency_exchange_rates.base)

        for quote, rate_info in currency_exchange_rates.quotes.items():
            quote_to_rate_info = {quote.value: json.dumps(jsonable_encoder(rate_info))}

            yield base_currency_storage_key, quote_to_rate_info
