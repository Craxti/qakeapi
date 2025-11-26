"""
Pipeline Processor - Function composition in pipelines.

This module provides functionality to compose functions into pipelines,
allowing data to flow through a series of processing steps.
"""

import inspect
from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar("T")


class Pipeline:
    """
    Pipeline for composing functions.
    
    Allows data to flow through a series of processing steps,
    with each step receiving the output of the previous step.
    """
    
    def __init__(self, steps: List[Callable[..., Any]]):
        """
        Initialize pipeline.
        
        Args:
            steps: List of functions to compose
            
        Example:
            ```python
            def validate(data):
                if not data:
                    raise ValueError("Data required")
                return data
            
            def transform(data):
                return {"id": data.get("id"), "name": data.get("name")}
            
            def save(data):
                # Save to database
                return data
            
            pipeline = Pipeline([validate, transform, save])
            result = await pipeline.execute({"id": 1, "name": "John"})
            ```
        """
        self.steps = steps
    
    async def execute(self, data: Any = None) -> Any:
        """
        Execute pipeline with data.
        
        Args:
            data: Input data
            
        Returns:
            Output from last pipeline step
        """
        result = data
        
        for step in self.steps:
            # Check if step is async
            if inspect.iscoroutinefunction(step):
                result = await step(result)
            else:
                # Sync function - import and use sync_to_async
                from .hybrid import run_hybrid
                result = await run_hybrid(step, result)
        
        return result
    
    def __call__(self, data: Any = None) -> Any:
        """Make pipeline callable."""
        import asyncio
        return asyncio.create_task(self.execute(data))


def pipeline(*steps: Callable[..., Any]) -> Pipeline:
    """
    Create pipeline from functions.
    
    Args:
        *steps: Functions to compose into pipeline
        
    Returns:
        Pipeline instance
        
    Example:
        ```python
        def validate(data):
            return data
        
        def transform(data):
            return {"id": data.get("id")}
        
        pipe = pipeline(validate, transform)
        result = await pipe.execute({"id": 1})
        ```
    """
    return Pipeline(list(steps))


def pipeline_decorator(*steps: Callable[..., Any]):
    """
    Pipeline decorator - wraps function with pipeline steps.
    
    Args:
        *steps: Pipeline steps to apply before function
        
    Example:
        ```python
        @pipeline_decorator(validate, authorize)
        def create_resource(data):
            return {"id": 1}
        
        # When create_resource is called, validate and authorize run first
        ```
    """
    def decorator(handler: Callable[..., Any]) -> Callable[..., Any]:
        async def wrapper(data: Any = None) -> Any:
            # Execute pipeline steps
            pipe = Pipeline(list(steps))
            result = await pipe.execute(data)
            
            # Execute handler
            if inspect.iscoroutinefunction(handler):
                return await handler(result)
            else:
                from .hybrid import run_hybrid
                return await run_hybrid(handler, result)
        
        return wrapper
    
    return decorator


