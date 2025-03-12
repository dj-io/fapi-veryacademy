<h1 align="center">FastAPI Production Ready Guide</h1>

<h3 align="center">Some code examples and notes to setup a web api using</h3>

<h3 align="center"> Docker + Postgresql + SQLAlchemy + Alembic + GRAPHQL or  REST + User Auth (JWT) & Security (RSA) </h3>


# Docker, PostgreSQL + Alembic + PGAdmin Setup

### Getting Started
- **mkdir `app-name`**
- **start virtual env** *(pip installs deps globally, not at project level - creating venv will scope deps to this project or any project using this venv as the python interpretor, best for avoiding dep conflicts)*
    ```sh
    python3 -m venv venv
    source venv/bin/activate
    ```
   -  **notes**
        - press `CMD + SHIFT + P` to open command pallette, type in select: python interpretor to manually select the directory venv if deps are not recognized automatically
- **Install the needed dependencies**
    - **REST**: pip3 install `fastapi` `fastapi-sqlalchemy` `pydantic` `alembic` *`psycopg2-binary`* `uvicorn[standard]` `python-dotenv` `pyJWT` `bcrypt`
    - **GRAPHQL**: pip3 install `fastapi` `uvicorn[standard]` `alembic` `psycopg2-binary` `python-dotenv` `pyJWT` `bcrypt` `starlette-graphene3` `rsa` `cryptography`
        - **In a seperate command**: pip3 install --pre `graphene-sqlalchemy`

    **Notes**:
    - For **Graphql** Copy *requirements.txt* from graphql very_fapi dir and run (deps work better without versions defined in req.txt)

        ```sh
        pip3 install -r requirements.txt
        ```
    - If not using apple silicon install `psycopg2` instead of `psycopg2-binary`
### Docker Compose
- create `docker-compose.yml`
- define containers *(grab reference from docker-compose.yml in graphql or rest)*
    - `db`
    - `pgadmin`
    - `app` -> requires Dockerfile ->
- Create a docker file: `Dockerfile` *(grab code from graphql/dockerfile)*
    - in terminal run `pip3 freeze > requirements.txt` to create a requirements.txt with all of the necessary installs
    - alternatively `copy the requirements.txt` deps and paste in new file (ideal as some of the graphene dep versions have conflicts)

**.env**
- create and add the necessary vars to a .env
    ```env
    DATABASE_URL=postgresql+psycopg2://postgres:<password>@db:5432/<db_name>
    DB_USER=postgres - or postgres user in container
    DB_CONTAINER_NAME=<db-container-name>
    APP_CONTAINER_NAME=<app-container-name>
    DB_PASSWORD=<password>
    DB_NAME=blog_db
    PGADMIN_EMAIL=<youremail>
    PGADMIN_PASSWORD=<password>
    PRIVATE_KEY_FILE="/certs/private.pem"
    PUBLIC_KEY_FILE="/certs/public.pem"
    ALGORITHM="RS256"
    ACCESS_TOKEN_EXPIRE_MINUTES=60
    ```

### Alembic
- init alembic migrations directory (we will use alembic to automate migrating our tables and data to our database)
    ```sh
    alembic init alembic
    ```
    - ensure you have defined a database url in .env
        - *i.e* `DATABASE_URL=postgresql+psycopg2://<username>:<password>@db:5432/<database_name>`
    - in alembic/env.py update env.py
        - load in the env variables
        ```python
            import os, sys
            from dotenv import load_dotenv

            # this is the .env path which provides access to the env variables

            # if alembic is was not initialized in the root dir or moved to a sub dir we add "../../" to explicitly set the root dir,
            # should go up as far as your root dir is from env.py this path goes up 2 levels
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__), "../../")) # path ref not needed if alembic/env.py is in the root dir!
            load_dotenv(os.path.join(BASE_DIR, ".env"))
            sys.path.append(BASE_DIR)

            # set an environment variable we want to access i.e DATABASE_URL
            config = context.config
            config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])
        ```
        - set the data to migrate

       **1. If all models are in one file**
        ```python
            import models # <- defined in REST or GRAPHQL section
            target_metadata = models.Base.metadata
        ```
        **2. If models are in multiple files**
        - We need to import and reference the unified Base var defined in the db config file (file we define the engine and init session) as this will contain all the metadata for our models/schemas throughout or application

        ```python
        from db_config import Base # <- defined in REST or GRAPHQL section
        target_metadata = Base.metadata
        ```


# SERVICES SETUP

<h1 align="center">CHOOSE YOUR PROTOCOL </h1>

### REST
- Create a `main.py` file
    ```python
    import uvicorn
    from fastapi import FastAPI

    app = FastAPI()

    @app.get('/')
    async def root():
        {"message": "hello world"}
    ```

- create a db_config.py file
    ```python
        import os
        from dotenv import load_dotenv
        from sqlalchemy import create_engine
        from sqlalchemy.orm import scoped_session, sessionmaker
        from sqlalchemy.ext.declarative import declarative_base

        load_dotenv(".env")
        SQLACHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

        engine = create_engine(
            SQLACHEMY_DATABASE_URL,
        )

        db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

        Base = declarative_base()
    ```

- Create a models.py file and import the deps
    ```python
        from db_config import Base
        from sqlalchemy.orm import relationship

        class Post(Base):
            __tablename__ = "post"

            id = Column(Integer, primary_key=True, index=True)
            title = Column(String)
            author = Column(String)
            content = Column(String)
            time_create = Column(DateTime(timezone=True), server_default=func.now())
            author_id = Column(Int, ForeignKey("author.id"))

            author = relationship("Author")
    ```
- Create a schemas.py file (define what data we should get and post to our database (response and request models))
    ```python
    from pydantic import BaseModel

        class Post(BaseModel):
            title: str
            author: str
            content: str
            author_id: int

            class Config:
                orm_mode = True

        class Author(BaseModel):
            name: str
            age: int

            class Config:
                orm_mode = True
    ```

### GRAPHQL (with [starlette-graphene3](https://github.com/ciscorn/starlette-graphene3))
- create a `main.py` file
    ```python
        import graphene
        from starlette.applications import Starlette
        from starlette_graphene3 import GraphQLApp, make_graphiql_handler


        app = Starlette()

        app.mount("/graphql", GraphQLApp(schema=graphene.Schema(), on_get=make_graphiql_handler()))


        # ------ larger applications -------

        # Merge queries (import from query dir)
        class Query("PostQuery, UserQuery", graphene.ObjectType):
            pass

        # Merge mutations (import from mutations dir)
        class Mutation("PostMutations, UserMutations", graphene.ObjectType):
            pass

        # Define GraphQL schema and pass entire
        app.mount(
            "/graphql",
            GraphQLApp(
                schema=graphene.Schema(
                    query=Query,
                    mutation=Mutation
                    ),
                    on_get=make_graphiql_handler() # runs the graphiql playground
            )
        )

    ```
    - confirm app mounted
        - in new browser tab enter `localhost:8000/graphql`

- create a db_config.py file
    ```python
        import os
        from dotenv import load_dotenv
        from sqlalchemy import create_engine
        from sqlalchemy.orm import scoped_session, sessionmaker
        from sqlalchemy.ext.declarative import declarative_base

        load_dotenv(".env")
        SQLACHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

        engine = create_engine(
            SQLACHEMY_DATABASE_URL,
        )

        db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

        Base = declarative_base()
    ```
- create a models.py file (larger application we would create models/post_models.py)
    ```python
        from sqlalchemy import Column, DateTime, Integer, String
        from sqlalchemy.sql import func

        from db_conf import Base

        class Post(Base):
            __tablename__ = "post"

            id = Column(Integer, primary_key=True, index=True)
            title = Column(String)
            author = Column(String)
            content = Column(String)
            time_create = Column(DateTime(timezone=True), server_default=func.now())
    ```

- create a schemas.py file
    ```python
        import graphene
        from pydantic import BaseModel
        from  models import Post

        # here is our request body/model, this will be used in the graphql mutation to send data to our db
        class PostSchema(BaseModel):
            title: str
            content: str
         # this is our response body/model it will be used to perform queries (get requests) from our db (we pass in all fields and the client can structure which fields to return)
        class PostModel(graphene.ObjectType): # graphql schema, inherits from graphene and uses it graphene to set field types
            id = graphene.ID() #id field
            title = graphene.String() # string field
            author = graphene.String()
            content = graphene.String()
            time_create = graphene.DateTime() #date time field
    ```
- create a queries.py file (larger application we would create queries/post_queries.py)
```python
    # defining a query class (larger projects would define it i.e PostQuery, UserQuery)
    class Query(graphene.ObjectType):
        all_posts = graphene.List(PostModel) # this defines the query name the client will use (allPosts) and the data the query returns
        post_by_id = graphene.Field(PostModel, post_id=graphene.Int(required=True)) # defining queryname (postById) and the data the query returns

        # all queries require resolvers -> think of this as the repository layer in REST API
        def resolve_all_posts(self, info): # the business logic for the query should match the query var prefixed with resolve
            return db.query(models.Post).all() #sqlalchemy query language

        def resolve_post_by_id(self, info, post_id):
            return db.query(models.Post).filter(models.Post.id == post_id).first() #sqlalchemy query language
```

- create a mutations.py file (larger application we would create mutations/post_mutations.py)
```python
     # defining a specific mutation for the post entity (defines a specific mutation/request body)
    class CreateNewPost(graphene.Mutation):
        class Arguments: # set the arguments we want to accept in our mutation (request body)
            title = graphene.String(required=True)
            content = graphene.String(required=True)

        ok = graphene.Boolean() # sets our mutation return

        # mutate in place of post method in http (preparing and setting data in db, may include some logic if needed)
        @staticmethod
        def mutate(root, info, title, content):
            post = PostSchema(title=title, content=content) # confirm data passed in matches what we expect in our schema
            db_post = models.Post(title=post.title, content=post.content) # prepare data to be added into the database
            db.add(db_post)
            db.commit()
            db.refresh(db_post)
            ok = True
            return CreateNewPost(ok=ok)

    # add our post mutations - mutations are how graphql defines a method that adds data
    class PostMutations(graphene.ObjectType):
        create_new_post = CreateNewPost.Field() # define name client will use to call mutation (CreateNewPost) set what mutation to be used
```
### GraphQL Client Request examples

- **create post mutation**
    - ```graphql
         mutation CreateNewPost {
            createNewPost(title: "title1" , content: "content1") { ok }
        }
      ```
- **get post query**
    ```graphql
        query {
            allPosts {
                # client decides what fields to return in this query
                title
                id
                content
            }
        }
    ```
- **get post by id query**
    ```graphql
        query {
            postById(postId: 2) {
                # client decides what fields to return in this query
                title
                id
                content
            }
        }
    ```

# User Authentication

### Getting started
- **Create User Model** (in models.py file)

    ```python
        from db_conf import Base # import from db config file created in protocol setup

        class User(Base):
        __tablename__ = 'user'

        id = Column(Integer, primary_key=True, index=True)
        username = Column(String, unique=True)
        password =  Column(String(255))
    ```
- **Create a user schema** (in schemas.py file) (will define the request body/data we want a client to pass in the query)
    ```python
        class UserSchema(BaseModel):
            username: str
            password: str
    ```
- **Create a CreateUser Mutation** (in mutations.py file)
    ```python
        View examples in GraphQL/main.py
    ```

### JWT + RSA Key Pairs
**Create a security dir `/security`**

- **Create an keyGeneratorUtil.py file**
```python
    View examples in security/key_generator.py
```

- **Create an auth.py file**

```python
    import os
    import models
    from datetime import datetime, timedelta, UTC
    from sqlalchemy.sql import func

    import jwt
    from dotenv import load_dotenv
    from security.keyGeneratorUtil import PRIVATE_KEY, PUBLIC_KEY

    load_dotenv(".env")

    # bring in rsa keys
    PRIVATE_KEY, PUBLIC_KEY = key_generator()

    # JWT Configurations
    ALGORITHM = os.environ["ALGORITHM"] # "RS256"

    def create_access_token(data, expires_delta):
        to_encode = data.copy()
        expire = datetime.now(UTC) + expires_delta
        to_encode.update({ "exp": expire })
        private_pem = PRIVATE_KEY.save_pkcs1().decode("utf-8")
        access_token = jwt.encode(to_encode, private_pem, algorithm=ALGORITHM)
        return access_token

    def decode_access_token(data):
        public_pem = PRIVATE_KEY.save_pkcs1().decode("utf-8")
        token_data = jwt.decode(data, public_pem, algorithms=ALGORITHM)
        return token_data

    def create_refresh_token():
        pass # generate refresh token

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
```

- **Create an `auth_schema.py` file (in schemas dir)**
```python
from dotenv import load_dotenv
from .security import create_access_token
from schemas import UserSchema
import models
from db_config import db

load_dotenv(".env")

ACCESS_TOKEN_EXPIRE_MINUTES = os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] # 60

class Token(graphene.ObjectType):
    access_token = graphene.String()
    token_type = graphene.String()

class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    token = graphene.String()

    @staticmethod
    def mutate(root, info, username, password):
        # confirm data passed in to mutation matches the schema we set
        user = UserSchema(username=username, password=password)
        # confirm user exists by matching username
        db_user_info = db.query(models.User).filter(models.User.username == username).first()
        # if username exists we check the password passed in against the password of the user in db
        if bcrypt.checkpw(user.password.encode("utf-8"), db_user_info.password.encode("utf-8")):
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(data={"user": username}, expires_delta=access_token_expires)
            ok = True
            return Login(token=Token(token=access_token, token_type="bearer"))
        else:
            ok = False
            return Login(ok=ok)
```

- **Now that our user has a token, we can decode the token in all further request to verify the requests are envoked by a user who is authenticated**

    - **Create a Query or Mutation only executable with token**
    ```python
     check graphql/main.py for examples
    ```

# Running the containers

- **Stand Up Containers**
    - in terminal run
        ```sh
        - docker-compose build
        - docker-compose up
        ```
    - Test the root endpoint `locahost:8000/` or `localhost:8000/graphql`
        - REST -> should display { message: "hello world" }
        - GRAPHQL -> graphiql playground
- **Run the initial migration** (migrates tables into database from our app container)

    **1. If alembic was initialized in the root dir**:
    ```sh
    - docker-compose run <app-container-name> alembic revision --autogenerate -m "Initial Migration"
    - docker-compose run <app-container-name> alembic upgrade head
    ```
    **2. If alembic was initialized or moved to a sub dir**:
    ```sh
    - docker-compose run <app-container-name> alembic -c <subdir>/alembic.ini revision --autogenerate -m "Initial Migration"
    - docker-compose run <app-container-name> alembic -c <subdir>/alembic.ini upgrade head
    ```
    - In alembic.ini change the script location `script_location = <sub-dir>/alembic`
    - In docker-compose change the app command `command: bash -c "alembic -c <subdir>/alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000 --reload`

- **test certs volume exists and keys are generated and persist**
    - run `docker volume ls` should output: `local     myproject_rsa_keys`
    - run `docker-compose down` then `docker-compose up`
    - run `docker ps` (grab the container id for app)
    - run `docker exec -it <container_id> ls /certs`
        - **output**: `private.pem public.pem`

- **Sign in to pgadmin**
    - access at http://127.0.0.1:`5050` (based on port set in yml config)
    - login using the credentials set in the .env
        - `PGADMIN_EMAIL=<email@email.com>`
        - `PGADMIN_PASSWORD=<password>`
    - right click servers and select register > server
        - navigate to connections
            - enter database service name (configured in yml)
            - enter the database username and password set in `.env`
            - select save

- **Access DB without PGAdmin**
    - **Terminal**
        - in a new terminal window run to get the postgres container name or ID
            ```sh
             docker ps
            ```
        - Open a shell inside the postgres container

            ```sh
             docker exec -it <db container name> psql -U postgres
            ```
            - **Now you can run your usual postgres queries**
                - Open database (run \l to list all databases)
                    ```sh
                    \c <db_name>
                    ```
                - use \q to quit

    - **Docker Desktop**
        - Go to Containers → Find your PostgreSQL container (e.g., my_postgres).
        - Click “Open in Terminal” (This is equivalent to running docker exec -it).



# Notes

### Including new dependencies in an existing container
- Any new libraries/packages installed will require a rerun of pip3 freeze > requirements.txt to update the txt then we will need to delete and recreate the container to include new dependencies (all data are persisted via volumes so removing containers are ok so long as the volumes are not removed)


### All code details are located in the mentioned files
**i.e for step: define docker commands to create an image for a python application**

- Navigate to the Dockerfile file and copy the code into the new project/application
