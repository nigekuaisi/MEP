import numpy as np
import pandas as pd
from algae_analysis.config.constants import PEAK_PHYSICS_DEF


class BeerLambertConstraintChecker:
    ABS_LINEAR_MIN = 0.001
    ABS_LINEAR_MAX = 1.8
    BASELINE_A680 = 0.05
    MAX_DENSITY_FOR_LOW_ABS = 0.3

    def __init__(self, peak_physics_def, algae_growth_rules, algae_name):
        self.peak_def = peak_physics_def or PEAK_PHYSICS_DEF
        self.algae_name = algae_name
        self.growth_rule = algae_growth_rules.get(algae_name,
                                                        algae_growth_rules[
                                                            list(algae_growth_rules.keys())[0]])

    def scattering_correction_analysis(self, raw_peaks):
        A730_raw = raw_peaks["A730"]
        corrected_result = {}
        for peak_name, config in self.peak_def.items():
            raw_abs = raw_peaks[peak_name]
            pure_abs = raw_abs - config["sca_dominant"] * A730_raw
            corrected_result[f"{peak_name}_raw"] = raw_abs
            corrected_result[f"{peak_name}_pure_abs"] = max(pure_abs, 1e-6)
        corrected_result["A730_pure_sca"] = A730_raw * self.peak_def["A730"]["sca_dominant"]
        return corrected_result

    def _in_range(self, val, minv=None, maxv=None):
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return False
        try:
            v = float(val)
        except:
            return False
        if minv is not None:
            try:
                if v < float(minv) - 1e-9:
                    return False
            except:
                pass
        if maxv is not None:
            try:
                if v > float(maxv) + 1e-9:
                    return False
            except:
                pass
        return True

    def growth_stage_identify(self, corrected_peaks):
        def safe_div(a, b):
            if b is None or (isinstance(b, float) and abs(b) < 1e-9) or np.isnan(b):
                return np.nan
            try:
                return float(a) / float(b)
            except:
                return np.nan

        R_680_480 = safe_div(corrected_peaks["A680_pure_abs"], corrected_peaks["A480_pure_abs"])
        R_abs_sca = safe_div(corrected_peaks["A680_pure_abs"], corrected_peaks["A730_pure_sca"])
        R_430_680 = safe_div(corrected_peaks["A430_pure_abs"], corrected_peaks["A680_pure_abs"])
        R_680_730 = safe_div(corrected_peaks["A680_raw"], corrected_peaks["A730_raw"])

        stage = "未知"
        if np.isnan(R_680_480):
            stage = "未知（比值计算异常）"
        else:
            if (not np.isnan(R_680_480) and R_680_480 < 0.5) and (not np.isnan(R_abs_sca) and R_abs_sca > 2.45):
                stage = "培养基 (空白对照)"
            else:
                used_dual = False
                dual_matched_stage = None
                if not np.isnan(R_680_480) and not np.isnan(R_abs_sca):
                    used_dual = True
                    rule = self.growth_rule
                    for phase in ["延迟期", "对数期", "稳定期", "衰亡期"]:
                        phase_rule = rule.get(phase, {})
                        r680_min = phase_rule.get("R_680_480_min", None)
                        r680_max = phase_rule.get("R_680_480_max", None)
                        rabs_min = phase_rule.get("R_abs_sca_min", None)
                        rabs_max = phase_rule.get("R_abs_sca_max", None)
                        if r680_min is None and r680_max is None and rabs_min is None and rabs_max is None:
                            continue
                        ok680 = self._in_range(R_680_480, r680_min, r680_max)
                        okabs = self._in_range(R_abs_sca, rabs_min, rabs_max)
                        if (r680_min is not None or r680_max is not None) and (
                                rabs_min is not None or rabs_max is not None):
                            if ok680 and okabs:
                                dual_matched_stage = phase
                                break
                        elif (r680_min is None and r680_max is None) and (rabs_min is not None or rabs_max is not None):
                            if okabs:
                                dual_matched_stage = phase
                                break
                        elif (rabs_min is None and rabs_max is None) and (r680_min is not None or r680_max is not None):
                            if ok680:
                                dual_matched_stage = phase
                                break
                if dual_matched_stage is not None:
                    stage = dual_matched_stage
                else:
                    rule = self.growth_rule
                    if "延迟期" in rule and rule["延迟期"].get("R_680_480_min") is not None and R_680_480 >= \
                            rule["延迟期"]["R_680_480_min"]:
                        stage = "延迟期"
                    elif "对数期" in rule and rule["对数期"].get("R_680_480_min") is not None and rule["对数期"].get(
                            "R_680_480_max") is not None and rule["对数期"]["R_680_480_min"] <= R_680_480 < \
                            rule["对数期"]["R_680_480_max"]:
                        stage = "对数期"
                    elif "稳定期" in rule and rule["稳定期"].get("R_680_480_min") is not None and rule["稳定期"].get(
                            "R_680_480_max") is not None and rule["稳定期"]["R_680_480_min"] <= R_680_480 < \
                            rule["稳定期"]["R_680_480_max"]:
                        stage = "稳定期"
                    elif "衰亡期" in rule and rule["衰亡期"].get("R_680_480_max") is not None and R_680_480 < \
                            rule["衰亡期"]["R_680_480_max"]:
                        stage = "衰亡期"
                    else:
                        stage = "过渡期 (边界值)"
        return {
            "Growth_Stage": stage,
            "R_680_480": round(R_680_480, 4) if not np.isnan(R_680_480) else None,
            "R_abs_sca": round(R_abs_sca, 4) if not np.isnan(R_abs_sca) else None,
            "R_430_680": round(R_430_680, 4) if not np.isnan(R_430_680) else None,
            "R_680_730": round(R_680_730, 4) if not np.isnan(R_680_730) else None,
        }

    def beer_lambert_soft_correction(self, raw_density, A680_raw):
        if pd.isna(raw_density) or pd.isna(A680_raw):
            return raw_density, "无修正"
        if A680_raw < self.BASELINE_A680 and raw_density > self.MAX_DENSITY_FOR_LOW_ABS:
            corrected_density = raw_density * (A680_raw / self.BASELINE_A680)
            return round(corrected_density, 6), "低吸光度高密度异常，已做软修正"
        elif raw_density < 0:
            return abs(raw_density), "负值取绝对值修正"
        else:
            return raw_density, "符合比尔 - 朗伯定律，无修正"