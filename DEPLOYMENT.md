# Smart Jal AI Backend Operations Guide

## Deployment

### Local Development (Recommended: Docker)
Since this project uses GIS libraries (GDAL, Rasterio) which are difficult to install on Windows, **using Docker is the highly recommended approach**.

1. Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
2. Set up your `.env` file with Supabase credentials.
3. Build and run the container:
   ```bash
   docker build -t smart-jal-backend .
   docker run -p 8000:8000 --env-file .env smart-jal-backend
   ```

4. **Alternative: Manual Installation (Advanced)**:
   > Requires C++ Build Tools and system-level GDAL.
   ```bash
   py -m pip install -r requirements.txt
   py -m uvicorn app.main:app --reload
   ```

### Production Deployment
The system is built for Kubernetes or high-availability cloud platforms. 
Use the provided `Dockerfile` which uses `Gunicorn` with `UvicornWorker` for production parallelism.

## API Documentation
Once running, access interactive documentation at:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## Database Admin (Supabase)
Ensure the following SQL migrations are applied in the Supabase SQL Editor:
- `backend/database/migrations/20240109_initial_schema.sql`

## Monitoring
- Check FastAPI logs for ingestion status.
- Audit logs are stored in the `audit_logs` table for critical system actions.
