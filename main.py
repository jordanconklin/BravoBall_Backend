"""
main.py
Main entry point of application that initializes the FastAPI app and includes all endpoints
"""

import os
from fastapi import FastAPI
import sentry_sdk
from routers import login, delete_account, onboarding, drills, session, drill_groups, data_sync_updates, saved_filters, profile, mental_training, custom_drills, store

# Initialize Sentry before FastAPI app (for error tracking)
# Set SENTRY_DSN environment variable in Render dashboard
sentry_dsn = os.getenv("SENTRY_DSN")
if sentry_dsn:
    sentry_sdk.init(
        dsn=sentry_dsn,
        # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring
        # Reduce this value in production if you want to reduce performance data volume
        traces_sample_rate=1.0,
        # Enable sending default PII (personally identifiable information) like user IP
        send_default_pii=True,
        # Set environment (staging, production, etc.)
        environment=os.getenv("ENVIRONMENT", "production"),
    )

# Initialize FastAPI app and router for endpoints
app = FastAPI()

# Include routers for endpoints in FastAPI app
app.include_router(login.router)
app.include_router(onboarding.router)
app.include_router(delete_account.router)
app.include_router(drills.router)
app.include_router(data_sync_updates.router)
app.include_router(session.router)
app.include_router(drill_groups.router)
app.include_router(saved_filters.router)
app.include_router(profile.router)
app.include_router(mental_training.router)
app.include_router(custom_drills.router)
app.include_router(store.router)

# Run FastAPI on local host
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
    # USE THIS IN TERMINAL FOR IPHONE TESTING
    # uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    