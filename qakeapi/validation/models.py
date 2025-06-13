import inspect
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union, get_type_hints

from pydantic import BaseModel, ValidationError

from ..core.requests import Request
from ..core.responses import JSONResponse, Response

T = TypeVar("T", bound=BaseModel)


def validate_request_body(model: Type[BaseModel]):
    """Decorator to validate request body against a Pydantic model"""

    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
            try:
                body = await request.json()
                validated_data = model(**body)
                request.validated_data = validated_data
                return await handler(request, *args, **kwargs)
            except ValidationError as e:
                return JSONResponse({"detail": e.errors()}, status_code=422)
            except ValueError:
                return JSONResponse({"detail": "Invalid JSON"}, status_code=400)

        return wrapper

    return decorator


def validate_response_model(model: Type[BaseModel]):
    """Decorator to validate response data against a Pydantic model"""

    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        async def wrapper(*args: Any, **kwargs: Any) -> Response:
            response = await handler(*args, **kwargs)

            if isinstance(response, Response):
                return response

            try:
                validated_data = model(**response)
                return JSONResponse(validated_data.model_dump())
            except ValidationError as e:
                return JSONResponse(
                    {"detail": "Response validation failed", "errors": e.errors()},
                    status_code=500,
                )

        return wrapper

    return decorator


def validate_path_params(**param_models: Type[BaseModel]):
    """Decorator to validate path parameters against Pydantic models"""

    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
            try:
                validated_params = {}
                for param_name, model in param_models.items():
                    if param_name in request.path_params:
                        validated_params[param_name] = model(
                            **{param_name: request.path_params[param_name]}
                        )
                request.validated_path_params = validated_params
                return await handler(request, *args, **kwargs)
            except ValidationError as e:
                return JSONResponse({"detail": e.errors()}, status_code=422)

        return wrapper

    return decorator


def validate_query_params(model: Type[BaseModel]):
    """Decorator to validate query parameters against a Pydantic model"""

    def decorator(handler: Callable) -> Callable:
        @wraps(handler)
        async def wrapper(request: Request, *args: Any, **kwargs: Any) -> Response:
            try:
                # Convert multi-value dict to single-value dict
                query_params = {
                    key: value[0] if len(value) == 1 else value
                    for key, value in request.query_params.items()
                }
                validated_data = model(**query_params)
                request.validated_query_params = validated_data
                return await handler(request, *args, **kwargs)
            except ValidationError as e:
                return JSONResponse({"detail": e.errors()}, status_code=422)

        return wrapper

    return decorator


class RequestModel(BaseModel):
    """Base class for request validation models"""

    class Config:
        extra = "forbid"


class ResponseModel(BaseModel):
    """Base class for response validation models"""

    class Config:
        extra = "allow"


def create_model_validator(*decorators: Callable) -> Callable:
    """Combine multiple validation decorators"""

    def decorator(handler: Callable) -> Callable:
        for decorator in reversed(decorators):
            handler = decorator(handler)
        return handler

    return decorator
