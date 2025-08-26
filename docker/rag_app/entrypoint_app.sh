#!/bin/bash
set -e

export APP_ENV="$PWD/${APP_ENV}"
exec poetry run app