"""
Gerenciador de configurações e preferências persistentes (config.json).
"""
import os
import json
from typing import Dict, Any

CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "active_tab": "Modo 1: Espaçamento Uniforme",
    "uniform_submode": "Por Intervalo de Tempo",
    "uniform_interval": 5.0,
    "uniform_count": 20,
    "burst_cycle": 30.0,
    "burst_count": 5,
    "burst_spacing": 0.5,
    "burst_offset": 0.0,
    "format": "PNG",
    "jpeg_quality": 95,
    "prefix": "print",
    "random_count": 15,
    "refine_window": 2.0,
    "refine_count": 5
}

def load_config() -> Dict[str, Any]:
    """Carrega as configurações do arquivo JSON ou retorna os padrões de fábrica."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Mescla com os padrões caso falte alguma chave
            merged = DEFAULT_CONFIG.copy()
            merged.update(data)
            return merged
    except Exception as e:
        print(f"Erro ao ler config.json: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config_data: Dict[str, Any]) -> bool:
    """Salva o dicionário de configurações em config.json."""
    try:
        current = load_config()
        current.update(config_data)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar config.json: {e}")
        return False

def reset_to_defaults() -> Dict[str, Any]:
    """Restaura as configurações de fábrica e salva no arquivo."""
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()
