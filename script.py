import os
import sys
import threading
import time
import subprocess

# 🧠 Parse token from command-line argument
TOKEN = None
for arg in sys.argv:
    if arg.startswith("token="):
        TOKEN = arg.split("=", 1)[1]

if not TOKEN:
    print("❌ Error: You must pass token like `python start.py token=YOUR_TOKEN`")
    sys.exit(1)

BASE_FOLDER = "nabil"
DOWNLOAD_DIR = "downloads"

def run_cmd(cmd):
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {cmd}")
    return result

def setup_environment():
    print("📦 Installing Zrok")
    run_cmd("curl -sSL https://get.openziti.io/install.bash | bash -s zrok")

    print("🔐 Enabling Zrok (headless)")
    run_cmd(f"zrok enable --headless {TOKEN}")

    print("📁 Cloning SD WebUI Forge")
    os.chdir("/kaggle/working")
    run_cmd(f"git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git {BASE_FOLDER}")
    os.chdir(BASE_FOLDER)

def download_all_models():
    print("📦 Downloading model files")
    folders = {
        "controlnet": "models/ControlNet",
        "controlnet1.1.txt": "models/ControlNet",
        "lora.txt": "models/Lora",
        "embeddings.txt": "embeddings",
        "preprocessor.txt": "models/ControlNetPreprocessor",
    }

    for file_name, target_folder in folders.items():
        file_path = os.path.join(DOWNLOAD_DIR, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                for url in f:
                    url = url.strip()
                    if url and not url.startswith("#"):
                        print(f"⬇️ {file_name} → {target_folder}")
                        run_cmd(f'wget --content-disposition -P "{target_folder}" "{url}"')
        else:
            print(f"⚠️ Skipping missing file: {file_name}")

def run_webui():
    while True:
        print("🚀 Launching Stable Diffusion WebUI...")
        exit_code = os.system("python3 launch.py --listen --port 7860 --xformers --enable-insecure-extension-access")
        print(f"❌ WebUI exited with code {exit_code}. Restarting...")

def start_webui_thread():
    threading.Thread(target=run_webui).start()
    print("⏳ Waiting for WebUI to initialize...")
    time.sleep(20)

def start_zrok_share():
    print("🌐 Creating Zrok share")
    run_cmd('zrok share public --headless "http://localhost:7860"')

# 🔁 Execute all steps
setup_environment()
download_all_models()
start_webui_thread()
start_zrok_share()
