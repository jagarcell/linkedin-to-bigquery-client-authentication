import subprocess
import sys
import shutil
import build_env

def set_env():
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
        "services",
        "update", 
        service_name,
        "--region", 
        region,
        "--env-vars-file", 
        env_file
    ]

    print(f"🚀 Setting environment variables for {service_name} in {region}...")
    try:
        # Run command and stream output
        result = subprocess.run(command, check=True, text=True, capture_output=False)
        print("✅ Environment variables set successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Setting environment variables failed.")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    set_env()
