installation steps:
> python -m venv venv
> source venv/bin/activate
> pip install -r ./requirements.txt

how to run:
> python ./app.py
or, if you want to specify some port and host you might start the server using the following command in the console:
> flask run -h localhost -p 8000

make sure that host and port specified here are the same as TARGET_URL from chromeextensions/constants.js, or update it accordingly
