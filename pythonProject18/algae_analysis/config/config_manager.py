import json
import os
from .constants import (
    CONFIG_FILE, DEFAULT_ALGAE_GROWTH_STAGE_RULES,
    ALLOWED_THRESHOLD_KEYS
)


def load_growth_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            cleaned_config = {}
            for algae_name, stages in loaded_config.items():
                default_algae = DEFAULT_ALGAE_GROWTH_STAGE_RULES.get(algae_name, None)
                if not default_algae:
                    continue
                cleaned_stages = {}
                for stage_name, default_params in default_algae.items():
                    loaded_params = stages.get(stage_name, {})
                    cleaned_params = {}
                    for param_key in default_params.keys():
                        if param_key in ALLOWED_THRESHOLD_KEYS:
                            cleaned_params[param_key] = loaded_params.get(param_key, default_params[param_key])
                    for k in default_params.keys():
                        if k not in cleaned_params:
                            cleaned_params[k] = default_params[k]
                    cleaned_stages[stage_name] = cleaned_params
                cleaned_config[algae_name] = cleaned_stages
            return cleaned_config
        except Exception:
            return DEFAULT_ALGAE_GROWTH_STAGE_RULES
    else:
        return DEFAULT_ALGAE_GROWTH_STAGE_RULES


def save_growth_config(config):
    try:
        cleaned = {}
        for algae_name, stages in config.items():
            cleaned_stages = {}
            for stage_name, params in stages.items():
                cleaned_params = {}
                for k, v in params.items():
                    if k in ALLOWED_THRESHOLD_KEYS:
                        cleaned_params[k] = v
                cleaned_stages[stage_name] = cleaned_params
            cleaned[algae_name] = cleaned_stages
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存配置失败：{e}")
        return False