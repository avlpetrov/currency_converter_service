Currency Converter Service
==========================
Installation
------------
This kind of installation is for development purpose only.
Install dependencies locally using ``poetry`` and ``make``: ::

    git clone https://github.com/avlpetrov/currency_converter_service
    cd currency_converter_service
    make install

Run  ``redis`` storage ::

    docker run --name dev-redis -d redis

Create ``.env`` file (or rename and modify ``.env.example``): ::

    echo DATABASE_URI=redis://localhost:6379 > .env

Run app: ::

    poetry run uvicorn --host=0.0.0.0 currency_converter_service.main:app --reload

API
----------
API routes available on ``/docs`` or ``/redoc`` paths with Swagger or ReDoc

Deployment
----------------------
Run app using ``docker`` and ``docker-compose``: ::

    docker-compose up
