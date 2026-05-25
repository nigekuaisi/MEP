import os
import pandas as pd
import numpy as np
from scipy.signal import savgol_filter
from algae_analysis.config.constants import (
    TARGET_PEAKS, SG_WINDOW_DEFAULT, SG_POLYORDER, SEARCH_RANGE_NM, PEAK_PHYSICS_DEF
)
from algae_analysis.core.physics_checker import BeerLambertConstraintChecker
from algae_analysis.config.config_manager import load_growth_config


# ================= CSV 格式标准化函数 =================
def normalize_csv_format(source_path, dest_path):
    encodings = ['utf-8', 'gbk', 'gb2312', 'utf-8-sig', 'latin-1']
    lines = None
    for encoding in encodings:
        try:
            with open(source_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            break
        except:
            continue
    if lines is None or len(lines) < 2:
        raise ValueError(f"CSV 行数不足：{source_path}")
    delimiter = ','
    sample_line = lines[0].strip()
    if '\t' in sample_line:
        delimiter = '\t'
    elif ';' in sample_line:
        delimiter = ';'
    has_metadata = False
    metadata_keywords = ["制造商名称", "设备名称", ">>>>>", "时间", "采样间隔", "积分时间", "平均次数", "型号"]
    for line in lines[:15]:
        for keyword in metadata_keywords:
            if keyword in line:
                has_metadata = True
                break
        if has_metadata:
            break
    if has_metadata:
        wavelength_row_idx = None
        absorbance_row_idx = None
        for i, line in enumerate(lines):
            if ">>>>>" in line:
                wavelength_row_idx = i + 1
                absorbance_row_idx = i + 2
                break
        if wavelength_row_idx is None:
            wavelength_row_idx = 9
            absorbance_row_idx = 10
        if wavelength_row_idx >= len(lines) or absorbance_row_idx >= len(lines):
            wavelength_row_idx = 0
            absorbance_row_idx = 1
    else:
        wavelength_row_idx = 0
        absorbance_row_idx = 1
    wavelength_line = lines[wavelength_row_idx].strip().split(delimiter)
    absorbance_line = lines[absorbance_row_idx].strip().split(delimiter)
    start_col = 0
    if len(wavelength_line) > 0:
        try:
            float(wavelength_line[0])
            start_col = 0
        except:
            start_col = 1
    wavelength_line = wavelength_line[start_col:]
    absorbance_line = absorbance_line[start_col:]
    wavelengths = pd.Series(pd.to_numeric(wavelength_line, errors="coerce")).dropna().values
    absorbances = pd.Series(pd.to_numeric(absorbance_line, errors="coerce")).dropna().values
    if len(wavelengths) == 0 or len(absorbances) == 0:
        raise ValueError(f"未能解析到有效数据：{source_path}")
    min_len = min(len(wavelengths), len(absorbances))
    with open(dest_path, 'w', encoding='utf-8', newline='') as f:
        f.write(','.join(str(w) for w in wavelengths[:min_len]) + '\n')
        f.write(','.join(str(a) for a in absorbances[:min_len]) + '\n')
    return True


# ================= 数据读取函数 =================
def read_data_simple(path):
    df = pd.read_csv(path, header=None)
    if df.shape[0] < 2:
        raise ValueError("CSV 行数不足")
    wavelengths = pd.to_numeric(df.iloc[0, :], errors="coerce").dropna().values
    absorbances = pd.to_numeric(df.iloc[1, :], errors="coerce").dropna().values
    min_len = min(len(wavelengths), len(absorbances))
    return pd.DataFrame({"Wavelength": wavelengths[:min_len], "Absorbance": absorbances[:min_len]})


# ================= 数据处理函数（核心修改） =================
def process_single_to_row(csv_path, concentration_val, algae_formula_func=None, algae_name=None, log_callback=None):
    # 加载全局配置
    growth_rules = load_growth_config()

    physics_checker = BeerLambertConstraintChecker(PEAK_PHYSICS_DEF, growth_rules, algae_name)
    df = read_data_simple(csv_path)
    df = df.sort_values("Wavelength").reset_index(drop=True)
    df = df[(df["Wavelength"] >= 200) & (df["Wavelength"] <= 1000)].reset_index(drop=True)
    if len(df) < 5:
        raise ValueError("有效数据点过少")
    window_length = min(SG_WINDOW_DEFAULT, len(df) - 1)
    if window_length % 2 == 0:
        window_length -= 1
    if window_length < 3:
        window_length = 3
    df["Absorbance_Smooth"] = savgol_filter(
        df["Absorbance"].values, window_length=window_length, polyorder=SG_POLYORDER
    )
    wavelengths = df["Wavelength"].values
    absorbances_smooth = df["Absorbance_Smooth"].values
    peak_values = {}
    for key, target_wl in TARGET_PEAKS.items():
        idx_nearest = int(np.argmin(np.abs(wavelengths - target_wl)))
        mask = (wavelengths >= target_wl - SEARCH_RANGE_NM) & (wavelengths <= target_wl + SEARCH_RANGE_NM)
        if np.sum(mask) > 0:
            rel_idx = int(np.argmax(absorbances_smooth[mask]))
            mask_idx = np.where(mask)[0]
            peak_idx = int(mask_idx[rel_idx])
            peak_abs = float(absorbances_smooth[peak_idx])
        else:
            peak_abs = float(absorbances_smooth[idx_nearest])
        peak_values[key] = peak_abs

    def safe_div(a, b):
        try:
            if b is None or np.isnan(b) or float(b) == 0.0:
                return np.nan
            return float(a) / float(b)
        except:
            return np.nan

    A430, A480, A680, A730 = [peak_values.get(k, np.nan) for k in ["A430", "A480", "A680", "A730"]]
    Ratio_680_730 = safe_div(A680, A730)
    Ratio_430_680 = safe_div(A430, A680)
    corrected_peaks = physics_checker.scattering_correction_analysis(peak_values)
    growth_fingerprint = physics_checker.growth_stage_identify(corrected_peaks)
    if log_callback:
        log_callback(
            f"【调试】{algae_name}样本{os.path.basename(csv_path)} - R_680_480={growth_fingerprint['R_680_480']}, R_abs_sca={growth_fingerprint['R_abs_sca']}, 判定生长期={growth_fingerprint['Growth_Stage']}",
            "PHYSICS")
    conc_out = np.nan
    if concentration_val is not None:
        try:
            conc_out = float(concentration_val)
        except:
            pass
    # 初始化返回值
    result = {
        "Sample_ID": os.path.splitext(os.path.basename(csv_path))[0],
        "Growth_Stage": growth_fingerprint["Growth_Stage"],
        "A430_raw": round(A430, 4),
        "A480_raw": round(A480, 4),
        "A680_raw": round(A680, 4),
        "A730_raw": round(A730, 4),
        "A430_pure_abs": round(corrected_peaks["A430_pure_abs"], 4),
        "A480_pure_abs": round(corrected_peaks["A480_pure_abs"], 4),
        "A680_pure_abs": round(corrected_peaks["A680_pure_abs"], 4),
        "A730_pure_sca": round(corrected_peaks["A730_pure_sca"], 4),
        "R_680_480": growth_fingerprint["R_680_480"],
        "R_abs_sca": growth_fingerprint["R_abs_sca"],
        "R_430_680": growth_fingerprint["R_430_680"],
        "R_680_730": growth_fingerprint["R_680_730"],
        "Concentration": conc_out,
        # 新增：统一字段，兼容单/双输出
        "Raw_Model_Density_Nanno": None,
        "Final_Density_Nanno": None,
        "Physics_Correction_Nanno": "无模型计算",
        "Raw_Model_Density_Chain": None,
        "Final_Density_Chain": None,
        "Physics_Correction_Chain": "无模型计算"
    }
    if algae_formula_func is not None:
        # 判断是否为混合藻类
        if algae_name == "混合藻类 (微拟球藻+链球藻)":
            # 双输出处理
            nanno_raw, chain_raw = algae_formula_func(A430, A480, A680, A730, Ratio_680_730, Ratio_430_680)
            # 处理微拟球藻
            result["Raw_Model_Density_Nanno"] = round(nanno_raw, 6) if not np.isnan(nanno_raw) else None
            final_nanno, note_nanno = physics_checker.beer_lambert_soft_correction(nanno_raw, A680)
            result["Final_Density_Nanno"] = final_nanno
            result["Physics_Correction_Nanno"] = note_nanno
            # 处理链球藻
            result["Raw_Model_Density_Chain"] = round(chain_raw, 6) if not np.isnan(chain_raw) else None
            final_chain, note_chain = physics_checker.beer_lambert_soft_correction(chain_raw, A680)
            result["Final_Density_Chain"] = final_chain
            result["Physics_Correction_Chain"] = note_chain
        else:
            # 单输出处理（兼容旧逻辑）
            raw_model_density = algae_formula_func(A430, A480, A680, A730, Ratio_680_730, Ratio_430_680)
            final_density, physics_correction_note = physics_checker.beer_lambert_soft_correction(raw_model_density,
                                                                                                  A680)
            if "微拟球藻" in algae_name:
                result["Raw_Model_Density_Nanno"] = round(raw_model_density, 6) if not np.isnan(
                    raw_model_density) else None
                result["Final_Density_Nanno"] = final_density
                result["Physics_Correction_Nanno"] = physics_correction_note
            else:
                result["Raw_Model_Density_Chain"] = round(raw_model_density, 6) if not np.isnan(
                    raw_model_density) else None
                result["Final_Density_Chain"] = final_density
                result["Physics_Correction_Chain"] = physics_correction_note
    return result