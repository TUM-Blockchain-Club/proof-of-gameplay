To get all the dependencies for the server you need to run:
```
poetry install
```

To start the server use:
```
poetry run python -m flask --app server run
```

To manualy verify the corresponding inputs for an id run:
```
poetry run python testClient.py
```

Verification only works if both video and input are provided

To recreate the database run:

```
poetry run python
from server import init\_db
init\_db()
```

