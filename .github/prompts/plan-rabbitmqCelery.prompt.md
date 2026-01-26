## Plan: Enable RabbitMQ & Celery Integration

The project already has a **complete Celery scaffolding** that's currently disabled. The work involves uncommenting existing configurations and enabling the services rather than building from scratch.

### Steps

1. **Enable Python dependencies** in [requirements.txt](requirements.txt): Uncomment `celery>=5.3.0` and `kombu>=5.3.0` lines.

2. **Enable Docker services** in [docker-compose.yml](docker-compose.yml): Uncomment the `rabbitmq`, `celery-worker`, and `celery-beat` service blocks (currently commented around lines 221-317), plus the `rabbitmq-data` volume.

3. **Enable Celery environment variables** in the `genovaai` service section of [docker-compose.yml](docker-compose.yml): Uncomment `CELERY_ENABLED=true` and `CELERY_BROKER_URL` environment variables.

4. **Update routes to use async tasks** in [routes/](routes/): Modify `analysis_routes.py` and `predictions_routes.py` to call tasks with `.delay()` instead of direct sync calls, returning task IDs for status polling.

5. **Add task status endpoint** in [routes/](routes/): Create an endpoint to check task status via `AsyncResult(task_id)` for client polling/webhooks.

6. **Test the integration**: Run `docker-compose up` and verify workers connect to RabbitMQ, tasks execute asynchronously, and results store in Redis.

### Further Considerations

1. **Task result polling vs WebSockets?** Current scaffolding supports polling. Do you want WebSocket-based real-time notifications instead?

2. **Beat schedule activation?** The `maintenance_tasks.py` has cleanup tasks ready. Should we enable scheduled tasks immediately or defer?

3. **Monitoring dashboard?** Consider adding Flower (`flower>=2.0.0`) for Celery task monitoring — should this be included?
