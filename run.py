import uvicorn
import os

if __name__ == "__main__":
    # Force clearing the environment variable if it exists
    # to ensure the app uses the .env file instead of the cached shell variable
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]
        
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
