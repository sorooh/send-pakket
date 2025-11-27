# Platform Core API Documentation

The Platform Core is the central nucleus of the Send-Pakket platform, providing merchant isolation, service management, configuration, events, and metrics for all tenant operations.

## Architecture Overview

- **PlatformCore**: Singleton instance managing global platform state
- **MerchantCore**: Individual merchant instances with isolated data and services
- **Core Services**: Available platform services (shipping, payment, analytics, etc.)
- **Configuration**: Hierarchical config system (global → merchant → service)
- **Events**: Centralized event logging and monitoring
- **Metrics**: Performance and business metrics collection

## API Endpoints

### Platform Core Management
- `GET /api/platform-core/` - Get platform core instance
- `GET /api/platform-core/stats/` - Get platform statistics
- `POST /api/platform-core/maintenance-mode/` - Enable/disable maintenance mode
- `POST /api/platform-core/update-stats/` - Update platform statistics

### Merchant Core Management
- `GET /api/merchant-cores/` - List merchant cores (tenant-filtered)
- `POST /api/merchant-cores/` - Create merchant core
- `GET /api/merchant-cores/{id}/` - Get merchant core details
- `PUT /api/merchant-cores/{id}/` - Update merchant core
- `DELETE /api/merchant-cores/{id}/` - Delete merchant core
- `POST /api/merchant-cores/{id}/activate/` - Activate merchant
- `POST /api/merchant-cores/{id}/suspend/` - Suspend merchant
- `GET /api/merchant-cores/{id}/limits/` - Check merchant limits
- `POST /api/merchant-cores/{id}/update-stats/` - Update merchant statistics

### Core Services
- `GET /api/core-services/` - List available services
- `GET /api/core-services/available/` - Get active services
- `GET /api/core-services/{id}/` - Get service details
- `POST /api/core-services/{id}/update-usage/` - Update service usage

### Merchant Services
- `GET /api/merchant-services/` - List merchant services (tenant-filtered)
- `POST /api/merchant-services/` - Create merchant service
- `GET /api/merchant-services/{id}/` - Get merchant service details
- `PUT /api/merchant-services/{id}/` - Update merchant service
- `DELETE /api/merchant-services/{id}/` - Delete merchant service
- `POST /api/merchant-services/{id}/toggle/` - Enable/disable service

### Configuration
- `GET /api/configurations/get-value/` - Get configuration value
- `POST /api/configurations/set-value/` - Set configuration value

### Events
- `GET /api/core-events/` - List events (tenant-filtered)
- `POST /api/core-events/` - Create event

### Metrics
- `GET /api/core-metrics/` - List metrics (tenant-filtered)
- `POST /api/core-metrics/` - Create metric
- `GET /api/core-metrics/summary/` - Get metrics summary

## Authentication

All endpoints require JWT authentication. Use `Authorization: Bearer <token>` header.

## Tenant Isolation

All endpoints automatically filter data by the authenticated user's company/merchant core. Cross-tenant access is prevented at the database query level.

## Example Requests

### Get Merchant Core
```bash
curl -H "Authorization: Bearer <token>" \
     http://localhost:8000/api/merchant-cores/
```

### Create Merchant Service
```bash
curl -X POST \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "core_service": "shipping",
       "is_enabled": true,
       "merchant_config": {"rate_limit": 100}
     }' \
     http://localhost:8000/api/merchant-services/
```

### Get Configuration Value
```bash
curl -H "Authorization: Bearer <token>" \
     "http://localhost:8000/api/configurations/get-value/?config_key=max_shipments_per_day"
```

## Services

### PlatformCoreService
- `get_platform_core()`: Get singleton platform instance
- `update_platform_stats()`: Update global statistics
- `set_maintenance_mode(enabled, message)`: Enable/disable maintenance

### MerchantCoreService
- `get_merchant_core(company)`: Get merchant core for company
- `create_merchant_core(data)`: Create new merchant core
- `activate_merchant(merchant_core)`: Activate merchant
- `suspend_merchant(merchant_core)`: Suspend merchant
- `check_merchant_limits(merchant_core)`: Check usage limits

### CoreServiceManager
- `get_available_services()`: Get active services
- `get_service_by_name(name)`: Get service by name
- `update_service_usage(service, merchant_core)`: Update usage counters
- `check_service_limits(service, merchant_core)`: Check rate limits

### CoreConfigurationService
- `get_config_value(key, scope, merchant_core, core_service)`: Get config value
- `set_config_value(key, value, scope, merchant_core, core_service)`: Set config value

### CoreEventService
- `log_event(type, level, title, description, merchant_core, core_service)`: Log event
- `get_recent_events(limit, event_type, merchant_core)`: Get recent events

### CoreMetricsService
- `record_metric(type, name, value, unit, merchant_core, core_service)`: Record metric
- `get_metrics_summary(name, type, merchant_core, hours)`: Get metrics summary
- `increment_metric(name, value, merchant_core, core_service)`: Increment counter
- `decrement_metric(name, value, merchant_core, core_service)`: Decrement counter

## Error Handling

- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Missing/invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found or cross-tenant access
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

Rate limits are enforced per merchant based on their configuration:
- API rate limits (requests per hour)
- Service-specific limits
- Monthly shipment limits

## Monitoring

All API calls are logged as events and metrics are recorded for:
- Request counts
- Error rates
- Performance metrics
- Business metrics (shipments, revenue, etc.)
