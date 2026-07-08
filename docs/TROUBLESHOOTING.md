# Troubleshooting Guide

## Common Issues

### Backend Issues

#### Database Connection Errors
- Verify `DATABASE_URL` is correct
- Check PostgreSQL is running
- Ensure database exists and migrations applied
- Check connection pool settings

#### Redis Connection Errors
- Verify `REDIS_URL` is correct
- Check Redis is running
- Verify network connectivity

#### Celery Worker Not Processing
- Check broker URL in celery config
- Verify workers are running: `celery -A app.workers.celery_app worker --loglevel=info`
- Check queue depth: `redis-cli LLEN celery`

### Frontend Issues

#### ECharts Not Rendering
- Check container has explicit height
- Verify data structure matches expectations
- Check theme context in Next.js

#### GSAP Animations Not Working
- Verify `prefers-reduced-motion` setting
- Check element refs are correct
- Ensure GSAP context is used for cleanup

#### Authentication Issues
- Check `NEXT_PUBLIC_API_URL`
- Verify token is not expired
- Check cookies/settings for refresh

## Logs

### Backend
```bash
# View logs
docker logs fraudwatch-backend

# Filter by level
docker logs fraudwatch-backend | grep ERROR
```

### Frontend
```bash
# Development
npm run dev

# Production logs
docker logs fraudwatch-frontend
```

## Performance

### Slow Queries
- Check database indexes
- Review query execution plans
- Enable query logging in development

### High Latency
- Check model inference time
- Review Celery task processing
- Monitor Redis memory usage

## Getting Help

- Check existing GitHub issues
- Review documentation
- Contact support team
