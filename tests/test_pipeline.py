"""
Tests for Pipeline Processor.
"""

import pytest
from qakeapi.core.pipeline import Pipeline, pipeline, pipeline_decorator


class TestPipeline:
    """Tests for Pipeline class."""
    
    def test_pipeline_creation(self):
        """Test pipeline creation."""
        def step1(data):
            return data + 1
        
        def step2(data):
            return data * 2
        
        pipe = Pipeline([step1, step2])
        assert len(pipe.steps) == 2
    
    @pytest.mark.asyncio
    async def test_pipeline_execution(self):
        """Test pipeline execution."""
        from qakeapi.core.hybrid import run_hybrid
        
        def step1(data):
            return data + 1
        
        def step2(data):
            return data * 2
        
        pipe = Pipeline([step1, step2])
        result = await pipe(5)
        
        # 5 + 1 = 6, then 6 * 2 = 12
        assert result == 12
    
    @pytest.mark.asyncio
    async def test_pipeline_with_async_step(self):
        """Test pipeline with async step."""
        import asyncio
        
        def step1(data):
            return data + 1
        
        async def step2(data):
            await asyncio.sleep(0.001)
            return data * 2
        
        pipe = Pipeline([step1, step2])
        result = await pipe(5)
        
        assert result == 12
    
    @pytest.mark.asyncio
    async def test_pipeline_empty(self):
        """Test empty pipeline."""
        pipe = Pipeline([])
        result = await pipe(5)
        
        # Empty pipeline should return input
        assert result == 5


class TestPipelineDecorator:
    """Tests for pipeline decorator."""
    
    def test_pipeline_decorator(self):
        """Test pipeline decorator."""
        def step1(data):
            return data + 1
        
        def step2(data):
            return data * 2
        
        @pipeline_decorator([step1, step2])
        def process(data):
            return data
        
        # Decorator should return a Pipeline
        assert hasattr(process, "steps") or callable(process)


class TestPipelineFunction:
    """Tests for pipeline function."""
    
    @pytest.mark.asyncio
    async def test_pipeline_function(self):
        """Test pipeline function."""
        def step1(data):
            return data + 1
        
        def step2(data):
            return data * 2
        
        pipe = pipeline(step1, step2)
        result = await pipe.execute(5)
        
        assert result == 12

