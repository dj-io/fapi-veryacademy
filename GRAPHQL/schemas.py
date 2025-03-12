import graphene
from pydantic import BaseModel
from models import Post

# request body should be pydantic type (this is use for mutations)
class PostSchema(BaseModel):
    title: str
    content: str

# response model/body must be a graphene response type (this is used for queries)
class PostModel(graphene.ObjectType):
    id = graphene.ID()
    title = graphene.String()
    author = graphene.String()
    content = graphene.String()
    time_create = graphene.DateTime()

# request body should be pydantic type (this is used for mutations)
class UserSchema(BaseModel):
    username: str
    password: str
