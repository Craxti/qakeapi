# QakeAPI Examples

This directory contains comprehensive examples demonstrating QakeAPI capabilities.

## 🚀 Quick Start

### Start All Examples
```bash
python start_all_apps.py
```

### Start Specific Categories
```bash
# Security examples
python security_examples_app.py

# Performance examples  
python performance_examples_app.py
```

### Run Tests
```bash
python run_all_tests.py
```

## 📋 Examples Overview

### 🔐 Security Examples
- **CSRF Protection** (`csrf_app.py`) - Cross-Site Request Forgery protection
- **XSS Protection** (`xss_app.py`) - Cross-Site Scripting protection  
- **SQL Injection Protection** (`sql_injection_app.py`) - SQL injection prevention

### ⚡ Performance Examples
- **Caching** (`caching_app.py`) - Response caching with TTL
- **Profiling** (`profiling_app.py`) - Performance profiling and monitoring
- **Optimization** (`optimization_app.py`) - Performance optimization techniques

### 🔧 Core Features
- **Basic CRUD** (`basic_crud_app.py`) - Basic Create, Read, Update, Delete operations
- **Authentication** (`auth_app.py`) - Session-based authentication
- **JWT Authentication** (`jwt_auth_app.py`) - JWT token-based authentication
- **Middleware** (`middleware_app.py`) - Custom middleware examples
- **Validation** (`validation_app.py`) - Request validation with Pydantic
- **File Upload** (`file_upload_app.py`) - File upload handling
- **WebSocket** (`websocket_app.py`) - Real-time WebSocket communication
- **Background Tasks** (`background_tasks_app.py`) - Asynchronous background processing
- **Rate Limiting** (`rate_limit_app.py`) - Request rate limiting
- **Dependency Injection** (`dependency_injection_app.py`) - Service dependency injection
- **OpenAPI/Swagger** (`openapi_app.py`) - Automatic API documentation

## 🌐 Port Mapping

| Application | Port | Description |
|-------------|------|-------------|
| basic_crud_app | 8001 | Basic CRUD operations |
| websocket_app | 8002 | WebSocket functionality |
| background_tasks_app | 8003 | Background task processing |
| rate_limit_app | 8004 | Rate limiting |
| caching_app | 8005 | Response caching |
| auth_app | 8006 | Session authentication |
| file_upload_app | 8007 | File upload handling |
| validation_app | 8008 | Request validation |
| jwt_auth_app | 8009 | JWT authentication |
| middleware_app | 8010 | Custom middleware |
| dependency_injection_app | 8011 | Dependency injection |
| profiling_app | 8012 | Performance profiling |
| openapi_app | 8013 | OpenAPI documentation |
| csrf_app | 8014 | CSRF protection |
| xss_app | 8015 | XSS protection |
| sql_injection_app | 8016 | SQL injection protection |
| optimization_app | 8017 | Performance optimization |

## 📖 Documentation

Each example includes:
- Comprehensive code comments
- API documentation via OpenAPI/Swagger
- Usage examples
- Best practices demonstration

## 🧪 Testing

Run comprehensive tests for all examples:
```bash
python run_all_tests.py
```

Test results show:
- ✅ Success rate percentage
- 📊 Individual app test results
- 🔍 Detailed error reporting

## 🔧 Configuration

### Environment Variables
- `DEBUG`: Enable debug mode
- `LOG_LEVEL`: Set logging level
- `PORT`: Override default port

### Dependencies
Install required packages:
```bash
pip install -r requirements.txt
```

## 🚀 Deployment

### Production Deployment
1. Set environment variables
2. Configure reverse proxy (nginx)
3. Use process manager (systemd, supervisor)
4. Enable SSL/TLS certificates

### Docker Deployment
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "start_all_apps.py"]
```

## 📊 Monitoring

### Health Checks
Each app provides `/health` endpoint:
```bash
curl http://localhost:8001/health
```

### Metrics
- Request/response times
- Error rates
- Resource usage
- Cache hit rates

## 🔒 Security Features

### Built-in Protection
- CSRF token validation
- XSS prevention
- SQL injection protection
- Rate limiting
- Input validation
- Secure headers

### Best Practices
- Use HTTPS in production
- Validate all inputs
- Implement proper authentication
- Regular security updates
- Monitor for vulnerabilities

## 📈 Performance Optimization

### Caching Strategies
- Response caching
- Database query caching
- Static asset caching
- CDN integration

### Optimization Techniques
- Async/await patterns
- Connection pooling
- Database indexing
- Load balancing
- Horizontal scaling

## 🤝 Contributing

### Adding New Examples
1. Create new app file
2. Add to appropriate category
3. Update port mapping
4. Add tests
5. Update documentation

### Code Standards
- Follow PEP 8
- Add type hints
- Include docstrings
- Write tests
- Update README

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/Craxti/qakeapi/issues)
- **Documentation**: [Wiki](https://github.com/Craxti/qakeapi/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/Craxti/qakeapi/discussions)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details. 