# Vehicle Frame Checker (Flask)

Deploy-ready Flask app for checking vehicle frame numbers.

## Deployment (e.g. Render / Railway)

```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```