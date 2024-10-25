
Requirements
- Docker
- Python

Setup Selenium

`docker run -d -p 4444:4444 -p 7900:7900 --shm-size="2g" selenium/standalone-chrome:latest`

Setup python environment

`python3 -m venv selenium_env`

`source selenium_env/bin/activate`

`pip install -r requirements.txt`

Run Test

`python3 test.py`
