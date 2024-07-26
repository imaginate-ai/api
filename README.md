### Useful commands:
- Creating the environment: `make local-setup`
- Entering the environment: `poetry shell`
- Leaving the environment: `exit`
- Installing libraries in the environment: `make install`
- Run the Flask application: `python imaginate_api/app.py`
- Encode / Decode .env via Bash: `cat decoded.env | base64 -w 0 > encoded.env` / `cat encoded.env | base64 --decode > decoded.env`
  - We could use this in the future for .env variables in our GitHub actions workflow; though we need to make sure .env is encoded as `utf-8` file or we will run into errors    
