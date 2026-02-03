import lmstudio as lms
import config, requests, time
from colorama import Fore, Style

config_lms = config.load_config()["lm_studio"]
lms.configure_default_client(config_lms["server_ip"])

def chat(content: str, temperature : int = 0.7, max_tokens: int = 1000) -> str:
    if not is_model_downloaded():
        download_model() #{'error': {'type': 'not_implemented', 'message': 'Specifying quantizations for downloading models with LM Studio Model Catalog identifiers is coming soon",'}}
    
    model = lms.llm(config_lms["model"])
    response = model.respond(
        content,
        config={
            "temperature": temperature,
            "maxTokens": max_tokens
        }
    )
    model.unload()
    return response

def is_model_downloaded() -> bool:
    model_key = config_lms["model_key"]
    models = lms.list_downloaded_models()
    for model in models:
        if model.model_key == model_key:
            return True
    return False

def download_model():
    ip = config_lms["server_ip"]
    url = f"http://{ip}/api/v1/models/download"
    body = {
        "model": config_lms["model"],
        "quantization": config_lms["model_variant"]
    }
    res = requests.post(url, json=body)

    if res.status_code == 501:
        print(Fore.RED + "Automatic download is still not implemented by LM Studio. Download the model manually in the GUI." + Style.RESET_ALL)

    if res.status_code != 200:
        raise Exception(res.json())
    
    if res.json().status != "downloading":
        raise Exception(res)
    
    wait_for_model()

def wait_for_model(timeout=600, poll_interval=2):
    start = time.time()
    while time.time() - start < timeout:
        if is_download_completed():
            return True
        time.sleep(poll_interval)
    raise TimeoutError("Model download did not complete in time")

def is_download_completed(job_id: str) -> bool:
    url = f"http://{ip}/api/v1/models/download/status/:{job_id}"
    res = requests.get(url).json()
    
    match res.status:
        case "downloading":
            print(f"Estimated time completion : {res.estimated_completion}")
            return False
        case "completed":
            return True
        case "failed" | "paused":
            raise Exception(res)