import json

import pytest
from aioredis import Redis
from async_asgi_testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_201_CREATED

from currency_converter_service.main import app


@pytest.mark.asyncio
async def test_client_receives_currency_conversion(database: Redis) -> None:
    await database.hmset_dict(
        "exchange-rates:USD",
        {"RUB": json.dumps({"rate": "79.7112", "last_updated": 1553178002})},
    )

    async with TestClient(app) as client:
        response = await client.get(
            "/convert",
            query_string={"from_currency": "USD", "to_currency": "RUB", "amount": "65"},
        )

    expected_response = {
        "last_updated": 1553178002,
        "from_currency": "USD",
        "to_currency": "RUB",
        "amount": "65",
        "rate": "79.7112",
        "conversion_result": "5181.2280",
    }

    assert response.status_code == HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.asyncio
async def test_client_loads_exchange_rates(database: Redis) -> None:
    async with TestClient(app) as client:
        response = await client.post(
            "/database",
            query_string={"merge": "0"},
            json={
                "currency_exchange_rates": [
                    {
                        "base": "USD",
                        "quotes": {
                            "RUB": {"rate": "79.75", "last_updated": 1584989828}
                        },
                    },
                ]
            },
        )

    expected_usd_exchange_rates = {
        b"RUB": json.dumps({"rate": "79.75", "last_updated": 1584989828}).encode(),
    }

    usd_exchange_rates = await database.hgetall("exchange-rates:USD")
    assert usd_exchange_rates == expected_usd_exchange_rates
    assert response.status_code == HTTP_201_CREATED


@pytest.mark.asyncio
async def test_client_merges_exchange_rates(database: Redis) -> None:
    await database.hmset_dict(
        "exchange-rates:USD",
        {
            "RUB": json.dumps({"rate": "79.7112", "last_updated": 1553178002}),
            "EUR": json.dumps({"rate": "0.920839", "last_updated": 1553178002}),
        },
    )

    async with TestClient(app) as client:
        response = await client.post(
            "/database",
            query_string={"merge": "1"},
            json={
                "currency_exchange_rates": [
                    {
                        "base": "USD",
                        "quotes": {
                            "RUB": {"rate": "79.75", "last_updated": 1584989828}
                        },
                    },
                ]
            },
        )

    usd_exchange_rates = await database.hgetall("exchange-rates:USD")

    expected_usd_exchange_rates = {
        b"RUB": json.dumps({"rate": "79.75", "last_updated": 1584989828}).encode(),
        b"EUR": json.dumps({"rate": "0.920839", "last_updated": 1553178002}).encode(),
    }

    assert usd_exchange_rates == expected_usd_exchange_rates
    assert response.status_code == HTTP_201_CREATED
