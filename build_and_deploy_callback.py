import subprocess
import sys
import shutil
import build_env # The build_env module contains project-specific constants

def deploy_callback():
    project_id = build_env.PROJECT_ID
    service_name = build_env.SERVICE_NAME
    region = build_env.REGION
    env_file = build_env.ENV_FILE

    # Try to locate gcloud automatically
    gcloud_path = shutil.which("gcloud")
    if not gcloud_path:
        print("Error: 'gcloud' command not found. Make sure Google Cloud SDK is installed and in your PATH.")
        sys.exit(1)

    command = [
        gcloud_path,
        "auth",
        "login"
    ]

    print(f"🚀 Building {service_name} for project {project_id}...")
    try:
        # Run command and stream output
        result = subprocess.run(command, check=True, text=True, capture_output=False)
        print("✅ Login completed successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Login failed.")
        print(f"Error: {e}")
        sys.exit(1)

    command = [
        gcloud_path,
        "config",
        "set",
        "project",
        project_id
    ]


    print(f"🚀 Setting project to {project_id}...")
    try:
        # Run command and stream output
        result = subprocess.run(command, check=True, text=True, capture_output=False)
        print("✅ Project set successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Project set failed.")
        print(f"Error: {e}")
        sys.exit(1)

    # The gcloud builds command
    command = [
        gcloud_path, 
        "builds", 
        "submit",
        "--tag", 
        f"gcr.io/{project_id}/{service_name}"
    ]

    print(f"🚀 Building {service_name} for project {project_id}...")
    try:
        # Run command and stream output
        result = subprocess.run(command, check=True, text=True, capture_output=False)
        print("✅ Build completed successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Build failed.")
        print(f"Error: {e}")
        sys.exit(1)

    # The gcloud deployment command
    command = [
        gcloud_path, 
        "run", 
        "deploy", 
        service_name,
        "--image", 
        f"gcr.io/{project_id}/{service_name}",
        "--region", 
        region,
        "--platform", 
        "managed",
        "--allow-unauthenticated",
        "--env-vars-file", 
        env_file
    ]

    print(f"🚀 Deploying {service_name} for project {project_id}...")
    try:
        # Run command and stream output
        result = subprocess.run(command, check=True, text=True, capture_output=False)
        print("✅ Deployment completed successfully.")
    except subprocess.CalledProcessError as e:
        print("❌ Deployment failed.")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    deploy_callback()
