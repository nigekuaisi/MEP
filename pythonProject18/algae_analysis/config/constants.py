# ================= 核心参数配置区 =================
NANNO_RAW_MIN = 1e-5
NANNO_RAW_MAX = 1.2
DENSITY_ZERO_THRESHOLD = 0.0005
TARGET_PEAKS = {"A430": 430, "A480": 480, "A680": 680, "A730": 730}
SG_WINDOW_DEFAULT = 15
SG_POLYORDER = 3
SEARCH_RANGE_NM = 20

# ================= 【双参数版】默认阈值 =================
DEFAULT_ALGAE_GROWTH_STAGE_RULES = {
    "链球藻 (原始精度版)": {
        "延迟期": {"R_680_480_min": 1.1, "R_abs_sca_max": 1.4},
        "对数期": {"R_680_480_min": 0.9, "R_680_480_max": 1.1, "R_abs_sca_min": 1.17, "R_abs_sca_max": 1.8},
        "稳定期": {"R_680_480_min": 0.7, "R_680_480_max": 0.9, "R_abs_sca_min": 1.6, "R_abs_sca_max": 2.2},
        "衰亡期": {"R_680_480_max": 0.7, "R_abs_sca_min": 2.0}
    },
    "微拟球藻 (原始精度版)": {
        "延迟期": {"R_680_480_min": 0.7, "R_abs_sca_max": 1.4},
        "对数期": {"R_680_480_min": 0.6, "R_680_480_max": 0.7, "R_abs_sca_min": 1.17, "R_abs_sca_max": 1.8},
        "稳定期": {"R_680_480_min": 0.55, "R_680_480_max": 0.6, "R_abs_sca_min": 1.6, "R_abs_sca_max": 2.2},
        "衰亡期": {"R_680_480_max": 0.55, "R_abs_sca_min": 2.0}
    }
}

CONFIG_FILE = "algae_growth_config_custom.json"
ALLOWED_THRESHOLD_KEYS = {"R_680_480_min", "R_680_480_max", "R_abs_sca_min", "R_abs_sca_max"}

# ================= 四峰物理特性参数 =================
PEAK_PHYSICS_DEF = {
    "A430": {"name": "叶绿素 a/b 强吸收峰", "abs_dominant": 0.98, "sca_dominant": 0.02, "type": "abs"},
    "A480": {"name": "类胡萝卜素吸收峰", "abs_dominant": 0.85, "sca_dominant": 0.15, "type": "abs"},
    "A680": {"name": "叶绿素 a 基准吸收峰", "abs_dominant": 0.99, "sca_dominant": 0.01, "type": "abs"},
    "A730": {"name": "细胞散射基准窗口", "abs_dominant": 0.05, "sca_dominant": 0.95, "type": "sca"}
}