import os, yaml

def deep_merge(dict1, dict2):
    if dict2 is None:
        return dict1

    for key, value in dict2.items():
        if (
            key in dict1
            and isinstance(dict1[key], dict)
            and isinstance(value, dict)
        ):
            dict1[key] = deep_merge(dict1[key], value)
        else:
            dict1[key] = value
    return dict1

def load_config(base_path="config.yaml", local_path="config.local.yaml"):
    with open(base_path, "r") as f:
        config = yaml.safe_load(f)

    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            local_config = yaml.safe_load(f)
        config = deep_merge(config, local_config)

    return config