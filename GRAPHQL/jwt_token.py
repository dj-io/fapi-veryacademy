import os
import jwt
import models
from datetime import datetime, UTC
from key_gen_util import key_generator
from jwt import PyJWTError
from graphql import GraphQLError
from dotenv import load_dotenv
from db_conf import db_session

load_dotenv(".env")

# bring in rsa keys
PRIVATE_KEY, PUBLIC_KEY = key_generator()

db = db_session.session_factory()

ALGORITHM = os.environ["ALGORITHM"]

def create_access_token(data, expires_delta):
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    to_encode.update({ "exp": expire })
    private_pem = PRIVATE_KEY.save_pkcs1().decode("utf-8")
    access_token = jwt.encode(to_encode, private_pem, algorithm=ALGORITHM)
    return access_token

def decode_access_token(data):
    public_pem = PUBLIC_KEY.save_pkcs1().decode("utf-8")
    token_data = jwt.decode(data, public_pem, algorithms=[ALGORITHM])
    return token_data

def authenticate_request(token): # call this in all requests that should only be executable with a valid token
    try:
        # update to confirm token is not expired and use refresh token to generate new token if so
        payload = decode_access_token(data=token)
        username = payload.get("user")

        if username is None:
            raise GraphQLError("Invalid credentials 1")
    except PyJWTError:
        raise GraphQLError("Invalid credentials 2")

    user = db.query(models.User).filter(models.User.username == username).first()

    if user is None:
        raise GraphQLError("Invalid Credentials 3")

    return user
