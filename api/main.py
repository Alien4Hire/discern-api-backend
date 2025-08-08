# main.py
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from api.routes import auth, agent, subscription, user, scripture, health
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Include routers
app.include_router(auth.router, tags=["Auth"])
app.include_router(user.router, tags=["User"])
app.include_router(agent.router, tags=["Agent"])
app.include_router(subscription.router, tags=["Subscription"])
app.include_router(scripture.router, tags=["Scripture"])
app.include_router(health.router, tags=["Health"])

# Define simple Bearer Token auth for Swagger UI
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Discern API",
        version="1.0.0",
        description="API for Discern spiritual assistant",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }

    # Apply BearerAuth to all routes
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
