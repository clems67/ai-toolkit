import lmstudio as lms
import config, requests, time
import os, re, time_method, json
from colorama import Fore, Style

config = config.load_config()["lm_studio"]

ip = config["server_api_host"]
remove_http = re.search(r"https?://(.+)", ip)
ip = remove_http.group(1)
lms.configure_default_client(ip)

chosen_config = config["config_chosen"]
config_lms = config[chosen_config]


@time_method.timed_decorator("LLM question")
def chat(content: str, structured_response: dict = None, temperature: float = 0.7, max_tokens: int = 1000,
         unload_when_finished=True) -> str:
    if not is_model_downloaded():
        download_model()  # {'error': {'type': 'not_implemented', 'message': 'Specifying quantizations for downloading models with LM Studio Model Catalog identifiers is coming soon",'}}

    smart_model_loading()

    res = execute_chat_request(content, structured_response, temperature, max_tokens)

    if is_context_window_too_small(res):
        unload_all_models()
        context_window_int = get_context_window_required(res) + max_tokens
        load_model(context_window_int)
        res = execute_chat_request(content, structured_response, temperature, max_tokens)

    if "error" in res:
        raise Exception(res["error"])

    save_response(res)

    if unload_when_finished:
        unload_all_models()

    return res


def smart_model_loading():
    """
    Manages active models by keeping only one instance that matches the
    configured model key and unloading all others to optimize resources.

    If the target model is not currently loaded, it triggers a new load.

    :return: None
    """
    models_match = []
    models_to_unload = []

    models = lms.list_loaded_models()
    identifiers = [model_id.identifier for model_id in models]
    for m in identifiers:
        match = re.search(r"^([a-z0-9\-_]+)(:\d+)?$", m)
        if match.group(1) == config_lms["model_key"]:
            models_match.append(m)
        else:
            models_to_unload.append(m)

    model_to_keep = models_match[0] if models_match else None
    models_to_unload.extend(models_match[1:])

    for model in models_to_unload:
        unload_model_by_id(model)
    if model_to_keep is None:
        load_model()


def execute_chat_request(content: str, structured_response: dict = None, temperature: float = 0.7,
                         max_tokens: int = 1000) -> str:
    body = {
        "model": config_lms["model"],
        "max_output_tokens": max_tokens
    }
    if structured_response:
        url = f"http://{ip}/v1/chat/completions"
        body["temperature"] = min(0.3, temperature)
        body["messages"] = [
            {"role": "system", "content": "You are a JSON-only assistant. Always return valid JSON."},
            {"role" : "user", "content" : content}]
        body["response_format"] = {
            "type" : "json_schema",
            "json_schema": {
                "strict": "true",
                "schema": {
                    "type" : "object",
                    "properties": structured_response
                }
            }
        }
    else:
        url = f"http://{ip}/api/v1/chat"
        body["temperature"] = temperature
        body["input"] = content

    return requests.post(url, json=body).json()


ERROR_PATTERN = re.compile(
    r"Cannot truncate prompt with n_keep \((?P<n_keep>\d+)\) >= n_ctx \((?P<n_ctx>\d+)\)"
)


def is_context_window_too_small(json) -> bool:
    if "output" in json:
        return False

    if "error" in json:
        message = json["error"]
        return ERROR_PATTERN.search(message) is not None


def get_context_window_required(error_json) -> int:
    try:
        message = error_json["error"]["message"]
    except (KeyError, TypeError):
        return None

    match = ERROR_PATTERN.search(message)

    return int(match.group("n_keep"))


def is_model_downloaded() -> bool:
    model_key = config_lms["model_key"]
    models = lms.list_downloaded_models()
    for model in models:
        if model.model_key == model_key:
            return True
    return False


def download_model():
    url = f"http://{ip}/api/v1/models/download"
    body = {
        "model": config_lms["model"],
        "quantization": config_lms["model_variant"]
    }
    res = requests.post(url, json=body)

    if res.status_code == 501:
        print(
            Fore.RED + "Automatic download is still not implemented by LM Studio. Download the model manually in the GUI." + Style.RESET_ALL)

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


def load_model(context_length: int | None = None):
    url = f"http://{ip}/api/v1/models/load"

    body = {
        "model": config_lms["model_key"],
        "offload_kv_cache_to_gpu": config_lms["offload_gpu"],
        "flash_attention": True,
    }

    if context_length is not None:
        body["context_length"] = context_length

    requests.post(url, json=body)


def save_response(res):
    folder_name = "data/llm_response"
    os.makedirs(folder_name, exist_ok=True)
    llm_response_path = f"{folder_name}/{time.strftime('%Y-%m-%d_%H-%M-%S')}"

    if "output" in res: #normal response
        res = str(res["output"][0]["content"])
        with open(f"{llm_response_path}.md", "w", encoding="utf-8") as f:
            f.write(res)
    else: #structured response
        res = res["choices"][0]["message"]["content"]
        res = json.loads(res)
        with open(f"{llm_response_path}.json", 'w', encoding="utf-8") as f:
            json.dump(res, f, indent=2)


    print(Fore.BLUE + f"LLM response has been saved here : " + Style.RESET_ALL + llm_response_path)


def unload_all_models():
    models = lms.list_loaded_models()
    for model in models:
        model.unload()


def unload_model_by_id(instance_id: str):
    url = f"http://{ip}/api/v1/models/unload"

    body = {
        "instance_id": instance_id
    }
    return requests.post(url, json=body).json()
