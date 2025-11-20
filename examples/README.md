# QakeAPI Examples

This directory contains comprehensive examples demonstrating various features of QakeAPI.

## 📚 Available Examples

### Basic Examples

1. **`basic_app.py`** - Basic QakeAPI application
   - Simple routes (GET, POST, PUT, DELETE)
   - Path parameters
   - Query parameters
   - Lifecycle events

2. **`simple_demo.py`** - Minimal example
   - Simplest possible QakeAPI app
   - Good starting point for beginners

### Advanced Examples

3. **`advanced_app.py`** - Advanced features
   - Authentication (JWT, API keys)
   - Data validation with Pydantic
   - WebSocket support
   - Dependency injection

4. **`complete_api_example.py`** - Complete API example
   - All features working together
   - Users and products CRUD
   - Authentication
   - Caching
   - Rate limiting
   - Monitoring
   - WebSocket

### Feature-Specific Examples

5. **`monitoring_example.py`** - Monitoring and metrics
   - Metrics collection
   - Health checks
   - Performance monitoring

6. **`caching_example.py`** - Caching
   - In-memory caching
   - Cache middleware
   - Cache invalidation
   - Cache statistics

7. **`rate_limiting_example.py`** - Rate limiting
   - Rate limit rules
   - Different limits for different endpoints
   - Rate limit statistics

8. **`database_example.py`** - Database connection pooling
   - Connection pool initialization
   - Transaction handling
   - Pool statistics

9. **`error_handling_example.py`** - Error handling
   - Custom exception handlers
   - Validation errors
   - HTTP errors
   - Error chaining

10. **`compression_example.py`** - Response compression
    - Automatic compression
    - Gzip and deflate
    - Compression thresholds

### Other Examples

11. **`validation_example.py`** - Data validation
    - Input validation
    - Custom validators
    - Validation errors

12. **`web_app.py`** - Web application
    - HTML templates
    - Static files
    - Forms handling

13. **`enhanced_app.py`** - Enhanced features
    - Multiple middleware
    - Error handling
    - Advanced routing

## 🚀 Running Examples

### Basic Example

```bash
python examples/basic_app.py
```

Then visit: http://localhost:8000

### Advanced Example

```bash
python examples/advanced_app.py
```

### Complete API Example

```bash
python examples/complete_api_example.py
```

### Feature-Specific Examples

```bash
# Monitoring
python examples/monitoring_example.py

# Caching
python examples/caching_example.py

# Rate Limiting
python examples/rate_limiting_example.py

# Database
python examples/database_example.py

# Error Handling
python examples/error_handling_example.py

# Compression
python examples/compression_example.py
```

## 📖 Documentation

After running any example, you can access:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 💡 Tips

1. **Start with `basic_app.py`** if you're new to QakeAPI
2. **Check `complete_api_example.py`** to see all features together
3. **Use feature-specific examples** to learn about specific functionality
4. **Read the code comments** - they explain what each part does

## 🔧 Customization

All examples are fully functional and can be customized:

- Change ports in `uvicorn.run()`
- Modify routes and endpoints
- Add your own middleware
- Integrate with real databases
- Add authentication logic

## 📝 Notes

- Examples use in-memory storage (not production-ready)
- Authentication tokens are simplified (use real JWT in production)
- Database examples require database setup
- Some examples require additional dependencies

## 🤝 Contributing

If you create a new example, please:

1. Add it to this README
2. Include docstrings explaining the example
3. Add comments for complex parts
4. Test that it runs correctly

