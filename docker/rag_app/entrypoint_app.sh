#!/bin/bash

export APP_ENV="$PWD/.env.local.docker"
cd /app/src
python main.py