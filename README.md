# musicrecs
A Spotify-powered music recommendation exchange web platform with snoozin 'n friends

# Running locally
## Requirements
- Linux
- python3

## Setup
- Make a spotify developer app through "https://developer.spotify.com/dashboard"
    - note the client id and client secret for your new app
- install sqlite with `apt-get install sqlite`
- Create a python3 virtual environment `python3 -m venv name-of-venv`
- Activate your virtual environment `source path-to-venv/bin/activate`
- Install required packages with `pip install -r requirements.txt`
- Create a flask 'secret key':
    ```python
    import secrets
    print(secrets.token_urlsafe(16))
    ```

# Run
- Activate your virtual environment `source path-to-venv/bin/activate`
- Set environment variables:
    ```bash
    export SPOTIPY_CLIENT_ID="insert-spotify-client-id-here"
    export SPOTIPY_CLIENT_SECRET="insert-spotify-client-secret-here"
    export SQLALCHEMY_DATABASE_URI="sqlite:////insert/database/file/path.db"
    export FLASK_SECRET_KEY="insert-your-secret-key"
    export FLASK_APP=musicrecs
    export FLASK_ENV=development
    ```
    - **note**: The sqlite database will be created at the path you specify upon the first run of the site.
- From the top level musicrecs directory, run: `flask run`
- Open "localhost:5000" in your browser
