import tkinter as tk
from tkinter import ttk, messagebox
import json
from algae_analysis.config.config_manager import load_growth_config, save_growth_config
from algae_analysis.config.constants import DEFAULT_ALGAE_GROWTH_STAGE_RULES


class GrowthConfigWindow:
    def __init__(self, parent, callback=None):
        self.top = tk.Toplevel(parent)
        self.top.title("生长期阈值配置（双参数 R_680_480 + R_abs_sca）")
        self.top.geometry("560x520")
        self.callback = callback

        # 这里需要重新加载一下，确保是最新的
        self.algae_growth_rules = load_growth_config()

        self.algae_list = list(self.algae_growth_rules.keys())
        self.current_algae = tk.StringVar(value=self.algae_list[0])
        self.entry_vars = {}
        self.create_widgets()
        self.load_current_config()

    def create_widgets(self):
        top_frame = ttk.Frame(self.top, padding=10)
        top_frame.pack(fill="x")
        ttk.Label(top_frame, text="选择藻类：", font=("Arial", 10, "bold")).pack(side="left")
        self.combo_algae = ttk.Combobox(
            top_frame,
            textvariable=self.current_algae,
            values=self.algae_list,
            state="readonly",
            width=30
        )
        self.combo_algae.pack(side="left", padx=10)
        self.combo_algae.bind("<<ComboboxSelected>>", self.on_algae_change)
        self.notebook = ttk.Notebook(self.top)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=5)
        self.stages = ["延迟期", "对数期", "稳定期", "衰亡期"]
        self.stage_frames = {}
        for stage in self.stages:
            frame = ttk.Frame(self.notebook, padding=15)
            self.notebook.add(frame, text=stage)
            self.stage_frames[stage] = frame
            self.create_stage_widgets(frame, stage)
        btn_frame = ttk.Frame(self.top, padding=10)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="💾 保存配置", command=self.save_config).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="↩️ 恢复默认", command=self.reset_default).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="❌ 关闭", command=self.top.destroy).pack(side="right", padx=10)

    def create_stage_widgets(self, parent, stage):
        algae = self.current_algae.get()
        config = self.algae_growth_rules[algae]
        stage_config = config.get(stage, {})
        for widget in parent.winfo_children():
            widget.destroy()
        info_text = {
            "延迟期": "注：配置【最小值】，更高的 R_680_480 与更低的 R_abs_sca 倾向延迟期（高浓度）",
            "对数期": "注：配置【最小值】和【最大值】，双参数区间内判定为对数期",
            "稳定期": "注：配置【最小值】和【最大值】，双参数区间内判定为稳定期",
            "衰亡期": "注：配置【最大值】，更低的 R_680_480 与更高的 R_abs_sca 倾向衰亡期（低浓度）",
        }
        ttk.Label(parent, text=info_text.get(stage, ""), foreground="gray", wraplength=500).pack(pady=(0, 10))
        kvs = [("R_680_480_min", "R_680/480 最小值"), ("R_680_480_max", "R_680/480 最大值"),
               ("R_abs_sca_min", "R_abs/sca 最小值"), ("R_abs_sca_max", "R_abs/sca 最大值")]
        for key, label in kvs:
            frame = ttk.Frame(parent)
            frame.pack(fill="x", pady=6)
            ttk.Label(frame, text=f"{label}：", width=20).pack(side="left")
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=20)
            entry.pack(side="left", padx=5)
            var_key = f"{algae}_{stage}_{key}"
            self.entry_vars[var_key] = var

    def on_algae_change(self, event):
        self.load_current_config()

    def load_current_config(self):
        algae = self.current_algae.get()
        config = self.algae_growth_rules[algae]
        for stage in self.stages:
            frame = self.stage_frames[stage]
            self.create_stage_widgets(frame, stage)
        for stage in self.stages:
            stage_config = config.get(stage, {})
            for param_key, value in stage_config.items():
                var_key = f"{algae}_{stage}_{param_key}"
                if var_key in self.entry_vars:
                    self.entry_vars[var_key].set(str(value))

    def save_config(self):
        # 使用全局变量名以便外部访问
        from algae_analysis.config import config_manager

        try:
            algae = self.current_algae.get()
            config = self.algae_growth_rules[algae]
            for stage in self.stages:
                stage_config = config.get(stage, {})
                for param_key in list(stage_config.keys()):
                    var_key = f"{algae}_{stage}_{param_key}"
                    if var_key in self.entry_vars:
                        value_str = self.entry_vars[var_key].get().strip()
                        if value_str == "":
                            continue
                        try:
                            stage_config[param_key] = float(value_str)
                        except ValueError:
                            messagebox.showerror("错误", f"{param_key} 必须为数字！")
                            return
            if save_growth_config(self.algae_growth_rules):
                # 更新内存中的全局变量（通过重新加载）
                # 注意：实际使用时最好用单例模式，这里为了兼容原代码逻辑
                import algae_analysis.config.config_manager as cm
                cm.ALGAE_GROWTH_STAGE_RULES = load_growth_config()

                messagebox.showinfo("成功", "阈值配置已保存！")
                if self.callback:
                    self.callback()
            else:
                messagebox.showerror("错误", "保存配置文件失败！")
        except Exception as e:
            messagebox.showerror("错误", f"保存失败：{e}")

    def reset_default(self):
        if messagebox.askyesno("确认", "确定要恢复默认阈值吗？"):
            self.algae_growth_rules = json.loads(json.dumps(DEFAULT_ALGAE_GROWTH_STAGE_RULES))
            save_growth_config(self.algae_growth_rules)
            self.load_current_config()
            messagebox.showinfo("成功", "已恢复默认阈值！")