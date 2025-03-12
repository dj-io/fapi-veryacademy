import os
import graphene
import bcrypt
import models
from dotenv import load_dotenv
from datetime import timedelta
from jwt_token import create_access_token, decode_access_token, authenticate_request
from starlette.applications import Starlette
from schemas import PostSchema, PostModel, UserSchema
from starlette_graphene3 import GraphQLApp, make_graphiql_handler
from db_conf import db_session
from graphql import GraphQLError
from jwt import PyJWTError



db = db_session.session_factory()
app = Starlette()

ACCESS_TOKEN_EXPIRE_MINUTES = os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"]


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
            access_token_expires = timedelta(minutes=60)
            access_token = create_access_token(data={"user": username}, expires_delta=access_token_expires)
            ok = True
            return Login(ok=ok, token=access_token)
        else:
            ok = False
            return Login(ok=ok)


class CreateNewUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info, username, password):
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()) # hash user password
        password_hash = hashed_password.decode("utf8") # ensures actual hash gets stored in database and not an encoded version of the hash

        user = UserSchema(username=username, password=password)
        db_user = models.User(username=user.username, password=password_hash)
        db.add(db_user)

        try:
            db.commit()
            db.refresh(db_user)
            db.close()
            return CreateNewUser(ok=True)
        except:
            db.rollback()
            raise


class Query(graphene.ObjectType):
    all_posts = graphene.List(PostModel)
    post_by_id = graphene.Field(PostModel, post_id=graphene.Int(required=True))

    def resolve_all_posts(self, info):
        return db.query(models.Post).all()

    def resolve_post_by_id(self, info, post_id):
        return db.query(models.Post).filter(models.Post.id == post_id).first()

# this mutation is only executable by a user that is logged in
class CreateNewPost(graphene.Mutation):
    class Arguments: # set the arguments we want to accept in our mutation (request body)
        title = graphene.String(required=True)
        content = graphene.String(required=True)
        token = graphene.String(required=True)

    result = graphene.String()

    ok = graphene.Boolean() # sets our mutation return

    @staticmethod
    def mutate(root, info, title, content, token):

        user = authenticate_request(token)

        if user:
            post = PostSchema(title=title, content=content) # confirm data passed in matches what we expect in our schema
            db_post = models.Post(title=post.title, content=post.content) # prepare data to be added into the database
            db.add(db_post)
            db.commit()
            db.refresh(db_post)
            result = "Added New Post"
            return CreateNewPost(result=result)

# register our mutations (equivelent of Post requests in REST Apis) - mutations are how graphql defines a method that adds data
class PostMutations(graphene.ObjectType):
    login = Login.Field()
    create_new_post = CreateNewPost.Field()
    create_new_user = CreateNewUser.Field()


app.mount("/graphql", GraphQLApp(schema=graphene.Schema(query=Query,mutation=PostMutations), on_get=make_graphiql_handler()))
