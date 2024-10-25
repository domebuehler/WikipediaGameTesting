# Wikipedia Game Testing 

## System Requirements
- Docker
- Python3

## Setup Selenium

`docker run -d -p 4444:4444 -p 7900:7900 --shm-size="2g" selenium/standalone-chrome:latest`

## Setup python environment

`python3 -m venv venv`

`source venv/bin/activate`

`pip install -r requirements.txt`

## Run tests

`python3 wikipedia_game_test.py`
