import os
import sys
import threading
import time
import subprocess

# 🧠 Parse token and download args
TOKEN = None
EXTRA_DOWNLOADS = {
    "stable-diffusion": [],
    "controlnet": [],
    "lora": [],
    "controlnetpreprocessor": [],
    "embeddings": [],
    "extension": [],
}

for arg in sys.argv:
    if arg.startswith("token="):
        TOKEN = arg.split("=", 1)[1]
    else:
        for category in EXTRA_DOWNLOADS:
            if arg.startswith(f"{category}="):
                urls = arg.split("=", 1)[1]
                for url in urls.split(","):
                    EXTRA_DOWNLOADS[category].append(url.strip())

if not TOKEN:
    print("❌ Error: You must pass token like `python flux.py token=YOUR_TOKEN`")
    sys.exit(1)

BASE_FOLDER = "nabil"
DOWNLOAD_DIR = "flux"

def run_cmd(cmd):
    print(f"🔧 Running: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"❌ Failed: {cmd}")
    return result

def setup_environment():
    print("📦 Installing Zrok")
    run_cmd("curl -sSL https://get.openziti.io/install.bash | bash -s zrok")

    run_cmd("zrok disable")
    
    print("🔐 Enabling Zrok (headless)")
    run_cmd(f"zrok enable --headless {TOKEN}")

    print("📁 Cloning SD WebUI Forge")
    os.chdir("/kaggle/working")
    run_cmd(f"git clone https://github.com/lllyasviel/stable-diffusion-webui-forge.git {BASE_FOLDER}")
    os.chdir(BASE_FOLDER)

def download_all_models():
    print("📦 Downloading model files")
    base_path = os.path.abspath(os.path.join(os.getcwd(), "..", DOWNLOAD_DIR))
    folders = {
        "controlnet.txt": "models/ControlNet",
        "lora.txt": "models/Lora",
        "embeddings.txt": "embeddings",
        "preprocessor.txt": "models/ControlNetPreprocessor",
    }

    extension_file = os.path.join(base_path, "extension.txt")
    if os.path.exists(extension_file):
        with open(extension_file, "r") as f:
            for url in f:
                url = url.strip()
                if url and not url.startswith("#"):
                    EXTRA_DOWNLOADS["extension"].append(url)
    else:
        print("⚠️ Skipping missing file: extension.txt")

    for file_name, target_folder in folders.items():
        file_path = os.path.join(base_path, file_name)
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                for url in f:
                    url = url.strip()
                    if url and not url.startswith("#"):
                        print(f"⬇️ {file_name} → {target_folder}")
                        run_cmd(f'wget --content-disposition -P "{target_folder}" "{url}"')
        else:
            print(f"⚠️ Skipping missing file: {file_name}")

def download_extra_urls():
    EXTRA_PATHS = {
        "stable-diffusion": "models/Stable-diffusion",
        "controlnet": "models/ControlNet",
        "lora": "models/Lora",
        "controlnetpreprocessor": "models/ControlNetPreprocessor",
        "embeddings": "embeddings",
    }

    for category, urls in EXTRA_DOWNLOADS.items():
        if category == "extension":
            continue  # handled separately
        target_dir = EXTRA_PATHS[category]
        os.makedirs(target_dir, exist_ok=True)
        for url in urls:
            print(f"⬇️ Extra download ({category}): {url}")
            run_cmd(f'wget --content-disposition -P "{target_dir}" "{url}"')

def clone_extensions():
    if not EXTRA_DOWNLOADS["extension"]:
        return
    os.makedirs("extensions", exist_ok=True)
    os.chdir("extensions")
    for url in EXTRA_DOWNLOADS["extension"]:
        name = url.rstrip("/").split("/")[-1].replace(".git", "")
        if os.path.exists(name):
            print(f"🔁 Extension already cloned: {name}")
            continue
        print(f"🧩 Cloning extension: {url}")
        run_cmd(f"git clone {url}")
    os.chdir("..")

def run_webui():
    while True:
        print("🚀 Launching Stable Diffusion WebUI...")
        exit_code = os.system(
            "python3 launch.py --listen --port 7860 --xformers --enable-insecure-extension-access"
        )
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
download_extra_urls()
clone_extensions()
start_webui_thread()
start_zrok_share()
