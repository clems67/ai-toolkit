import lmstudio as lms
import config, requests, time, os, re, json, time_method
from colorama import Fore, Style
from typing import Optional, Dict, Any

class LmStudio:
    """Main class for interacting with LM Studio API."""
    ERROR_PATTERN = re.compile(
        r"Cannot truncate prompt with n_keep \((?P<n_keep>\d+)\) >= n_ctx \((?P<n_ctx>\d+)\)"
    )
    content = None
    input_tokens = None
    total_output_tokens = None
    reasoning_output_tokens = None
    tokens_per_second = None
    time_to_first_token_seconds = None

    def __init__(self):
        """Initialize the LM Studio client."""
        self.config = config.load_config()["lm_studio"]
        self.ip = self._clean_ip_address(self.config["server_api_host"])
        lms.configure_default_client(self.ip)
        self.chosen_config = self.config["config_chosen"]
        self.config_lms = self.config[self.chosen_config]


    def _clean_ip_address(self, ip: str) -> str:
        """Remove http/https prefix from IP address."""
        remove_http = re.search(r"https?://(.+)", ip)
        return remove_http.group(1)

    @time_method.timed_decorator("LLM question")
    def chat(
        self,
        content: str,
        structured_response: Optional[Dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        unload_when_finished: bool = True
    ) -> str:
        """Send a chat request to LM Studio."""
        if not self.is_model_downloaded():
            self.download_model()

        self.smart_model_loading()

        res = self.execute_chat_request(content, structured_response, temperature, max_tokens)

        if self.is_context_window_too_small(res):
            self.unload_all_models()
            context_window_int = self.get_context_window_required(res) + max_tokens
            self.load_model(context_window_int)
            res = self.execute_chat_request(content, structured_response, temperature, max_tokens)

        if "error" in res:
            raise Exception(res["error"])

        self.save_response(res)
        self.extract_stats_info(res)

        if unload_when_finished:
            self.unload_all_models()

        return self.content

    def smart_model_loading(self) -> None:
        """Manages active models by keeping only one instance that matches the configured model key."""
        models_match = []
        models_to_unload = []

        models = lms.list_loaded_models()
        identifiers = [model_id.identifier for model_id in models]
        for m in identifiers:
            match = re.search(r"^([a-z0-9\-_]+)(:\d+)?$", m)
            if match.group(1) == self.config_lms["model_key"]:
                models_match.append(m)
            else:
                models_to_unload.append(m)

        model_to_keep = models_match[0] if models_match else None
        models_to_unload.extend(models_match[1:])

        for model in models_to_unload:
            self.unload_model_by_id(model)
        if model_to_keep is None:
            self.load_model()

    def execute_chat_request(
        self,
        content: str,
        structured_response: Optional[Dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Execute a chat request to LM Studio API."""
        body = {
            "model": self.config_lms["model"],
            "max_output_tokens": max_tokens
        }

        if structured_response:
            url = f"http://{self.ip}/v1/chat/completions"
            body["temperature"] = min(0.3, temperature)
            body["messages"] = [
                {"role": "system", "content": "You are a JSON-only assistant. Always return valid JSON."},
                {"role": "user", "content": content}
            ]
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "strict": "true",
                    "schema": {
                        "type": "object",
                        "properties": structured_response
                    }
                }
            }
        else:
            url = f"http://{self.ip}/api/v1/chat"
            body["temperature"] = temperature
            body["input"] = content

        return requests.post(url, json=body).json()

    def is_context_window_too_small(self, response: Dict[str, Any]) -> bool:
        """Check if the context window is too small for the current request."""
        if "output" in response:
            return False

        if "error" in response:
            message = response["error"]
            return self.ERROR_PATTERN.search(message) is not None
        return False

    def get_context_window_required(self, error_json: Dict[str, Any]) -> Optional[int]:
        """Get the required context window size from an error response."""
        try:
            message = error_json["error"]["message"]
        except (KeyError, TypeError):
            return None

        match = self.ERROR_PATTERN.search(message)
        if not match:
            return None
        return int(match.group("n_keep"))

    def is_model_downloaded(self) -> bool:
        """Check if the configured model is downloaded."""
        model_key = self.config_lms["model_key"]
        models = lms.list_downloaded_models()
        for model in models:
            if model.model_key == model_key:
                return True
        return False

    def download_model(self) -> None:
        """Download the configured model from LM Studio."""
        url = f"http://{self.ip}/api/v1/models/download"
        body = {
            "model": self.config_lms["model"],
            "quantization": self.config_lms["model_variant"]
        }
        res = requests.post(url, json=body)

        if res.status_code == 501:
            print(
                Fore.RED + "Automatic download is still not implemented by LM Studio. "
                "Download the model manually in the GUI." + Style.RESET_ALL
            )

        if res.status_code != 200:
            raise Exception(res.json())

        if res.json().status != "downloading":
            raise Exception(res)

        self.wait_for_model()

    def wait_for_model(self, timeout: int = 600, poll_interval: int = 2) -> None:
        """Wait for model download to complete."""
        start = time.time()
        while time.time() - start < timeout:
            if self.is_download_completed():
                return True
            time.sleep(poll_interval)
        raise TimeoutError("Model download did not complete in time")

    def is_download_completed(self, job_id: Optional[str] = None) -> bool:
        """Check if model download has completed."""
        url = f"http://{self.ip}/api/v1/models/download/status/:{job_id}"
        res = requests.get(url).json()

        match res.status:
            case "downloading":
                print(f"Estimated time completion: {res.estimated_completion}")
                return False
            case "completed":
                return True
            case "failed" | "paused":
                raise Exception(res)
        return False

    def load_model(self, context_length: Optional[int] = None) -> None:
        """Load the configured model into memory."""
        url = f"http://{self.ip}/api/v1/models/load"

        body = {
            "model": self.config_lms["model_key"],
            "offload_kv_cache_to_gpu": self.config_lms["offload_gpu"],
            "flash_attention": True,
        }

        if context_length is not None:
            body["context_length"] = context_length

        requests.post(url, json=body)

    def save_response(self, response: Dict[str, Any]) -> None:
        """Save the LLM response to a file."""
        folder_name = "data/llm_response"
        os.makedirs(folder_name, exist_ok=True)
        timestamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        llm_response_path = f"{folder_name}/{timestamp}"

        if "output" in response:  # normal response
            self.content = str(response["output"][0]["content"])
            with open(f"{llm_response_path}.md", "w", encoding="utf-8") as f:
                f.write(self.content)
        else:  # structured response
            raw_content = response["choices"][0]["message"]["content"]
            self.content = json.loads(raw_content)
            with open(f"{llm_response_path}.json", 'w', encoding="utf-8") as f:
                json.dump(self.content, f, indent=2)

        print(Fore.BLUE + f"LLM response has been saved here: " +
              Style.RESET_ALL + llm_response_path)

    def unload_all_models(self) -> None:
        """Unload all currently loaded models."""
        models = lms.list_loaded_models()
        for model in models:
            model.unload()

    def unload_model_by_id(self, instance_id: str) -> Dict[str, Any]:
        """Unload a specific model by its instance ID."""
        url = f"http://{self.ip}/api/v1/models/unload"
        body = {"instance_id": instance_id}
        return requests.post(url, json=body).json()

    def token_count(self, text: str) -> int:
        """Count the number of tokens in a given text."""
        return lms.llm().count_tokens(text)

    def extract_stats_info(self, response: Dict[str, Any]):
        if "stats" in response:
            self.input_tokens = response["stats"].get("input_tokens")
            self.total_output_tokens = response["stats"].get("total_output_tokens")
            self.reasoning_output_tokens= response["stats"].get("reasoning_output_tokens")
            self.tokens_per_second = response["stats"].get("tokens_per_second")
            self.time_to_first_token_seconds = response["stats"].get("time_to_first_token_seconds")