"""
Deployment script for FOR ME to Google Cloud Run

This script builds and deploys the FOR ME system as a Cloud Run service.

Usage:
    python deploy_to_cloud_run.py

Requirements:
    - Google Cloud Project with Cloud Run API enabled
    - Docker installed
    - gcloud CLI configured
"""

import os
import subprocess
import sys
from pathlib import Path

# Configuration
# PROJECT_ID must be set via GOOGLE_CLOUD_PROJECT environment variable
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
if not PROJECT_ID:
    raise ValueError(
        "GOOGLE_CLOUD_PROJECT environment variable is required. "
        "Set it in .env file or export it before running this script."
    )

REGION = os.getenv("CLOUD_RUN_REGION", "us-central1")
SERVICE_NAME = "for-me-agent"
IMAGE_NAME = f"gcr.io/{PROJECT_ID}/{SERVICE_NAME}"


def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def main():
    """Main deployment function."""
    print("=" * 70)
    print("FOR ME - Cloud Run Deployment")
    print("=" * 70)
    print(f"Project: {PROJECT_ID}")
    print(f"Region: {REGION}")
    print(f"Service: {SERVICE_NAME}")
    print(f"Image: {IMAGE_NAME}")

    # Check if Docker is available
    try:
        run_command(["docker", "--version"], check=False)
    except FileNotFoundError:
        print("❌ Docker not found. Please install Docker first.")
        sys.exit(1)

    # Build and push using Cloud Build (handles platform automatically)
    print("\n📦 Building Docker image using Cloud Build...")
    run_command(
        [
            "gcloud",
            "builds",
            "submit",
            "--tag",
            IMAGE_NAME,
            "--project",
            PROJECT_ID,
            ".",
        ]
    )

    # Deploy to Cloud Run
    print("\n☁️  Deploying to Cloud Run...")
    result = run_command(
        [
            "gcloud",
            "run",
            "deploy",
            SERVICE_NAME,
            "--image",
            IMAGE_NAME,
            "--platform",
            "managed",
            "--region",
            REGION,
            "--allow-unauthenticated",
            "--memory",
            "2Gi",
            "--cpu",
            "2",
            "--timeout",
            "300",
            "--max-instances",
            "10",
        ]
    )

    # Get service URL
    print("\n🔍 Getting service URL...")
    result = run_command(
        [
            "gcloud",
            "run",
            "services",
            "describe",
            SERVICE_NAME,
            "--region",
            REGION,
            "--format",
            "value(status.url)",
        ]
    )

    service_url = result.stdout.strip()

    print("\n" + "=" * 70)
    print("✅ DEPLOYMENT COMPLETE!")
    print("=" * 70)
    print(f"\nService URL: {service_url}")
    print(f"\nTest the service:")
    print(f'curl -X POST {service_url}/analyze \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"user_id": "test", "ingredient_text": "AQUA, GLYCERIN"}\'')


if __name__ == "__main__":
    main()

