from decimal import Decimal

from aioredis import Redis
from fastapi import Depends, FastAPI, HTTPException, Query
from starlette.responses import RedirectResponse
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)

from currency_converter_service.config import APP_NAME, DATABASE_URI, DEBUG
from currency_converter_service.currency import Currency
from currency_converter_service.currency_converter import calculate_conversion
from currency_converter_service.dependencies import (
    CurrencyExchangeRatesStorage,
    create_connection_pool,
    preprocess,
)
from currency_converter_service.models import (
    CurrencyExchangeConvertResponse,
    CurrencyExchangeLoadResponse,
    CurrencyExchangeRatesLoadRequest,
)

app: FastAPI = FastAPI(title=APP_NAME, debug=DEBUG)

connection_pool: Redis
currency_exchange_rates_storage: CurrencyExchangeRatesStorage


@app.on_event("startup")
async def startup() -> None:
    global connection_pool
    connection_pool = await create_connection_pool(DATABASE_URI)

    global currency_exchange_rates_storage
    currency_exchange_rates_storage = CurrencyExchangeRatesStorage(connection_pool)


@app.on_event("shutdown")
async def shutdown() -> None:
    global connection_pool
    connection_pool.close()
    await connection_pool.wait_closed()


async def database_connection_pool() -> Redis:
    return connection_pool


@app.get(
    "/convert",
    response_model=CurrencyExchangeConvertResponse,
    dependencies=[Depends(database_connection_pool)],
)
async def convert_currency(
    from_currency: Currency, to_currency: Currency, amount: Decimal = Query(..., gt=0),
) -> CurrencyExchangeConvertResponse:
    if from_currency == to_currency:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Choose different currencies",
        )

    exchange_rate = await currency_exchange_rates_storage.fetch_exchange_rate(
        base_currency=from_currency, quote_currency=to_currency
    )
    if not exchange_rate:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=(
                f"No exchange rates "
                f"for {from_currency.value}/{to_currency.value} currencies"
            ),
        )

    conversion_result = calculate_conversion(amount, exchange_rate.rate)

    response = CurrencyExchangeConvertResponse(
        from_currency=from_currency,
        to_currency=to_currency,
        amount=amount,
        rate=exchange_rate.rate,
        conversion_result=conversion_result,
        last_updated=exchange_rate.last_updated,
    )

    return response


@app.post(
    "/database",
    status_code=HTTP_201_CREATED,
    response_model=CurrencyExchangeLoadResponse,
    dependencies=[Depends(database_connection_pool)],
)
async def load_currency_exchange_rates(
    merge: bool, currency_exchange_rates: CurrencyExchangeRatesLoadRequest
):
    status = await currency_exchange_rates_storage.load_exchange_rates(
        loadable_exchange_rates=tuple(preprocess(currency_exchange_rates)), merge=merge
    )

    response = CurrencyExchangeLoadResponse(status=status, merge=merge)

    return response


@app.get("/")
async def redirect_to_docs() -> RedirectResponse:
    response = RedirectResponse(url="/docs")
    return response
