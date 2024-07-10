#!/bin/sh

git pull
alembic upgrade head
docker compose up --build -d