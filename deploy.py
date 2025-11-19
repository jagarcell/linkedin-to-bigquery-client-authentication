import subprocess
import sys
import shutil
import build_env

def deploy_service():
    service_name = build_env.SERVICE_NAME
    region = build_env.REGION
    env_file = build_env.ENV_FILE
    # Try to locate gcloud automatically
    gcloud_path = shutil.which("gcloud")
    if not gcloud_path:
        print("Error: 'gcloud' command not found. Make sure Google Cloud SDK is installed and in your PATH.")
        sys.exit(1)

    # The gcloud command
    command = [
        gcloud_path, 
        "run", 
        "deploy", 
        service_name,
        "--source", ".", 
        "--region", 
        region,
        "--allow-unauthenticated",
        "--env-vars-file", 
        env_file
    ]

    print(f"🚀 Deploying {service_name} to Cloud Run in {region}...")
    try:
        # Run command and stream output
        result = subprocess.run(command, check=True, text=True, capture_output=False)
        print("✅ Deployment completed successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Deployment failed.")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    deploy_service()
