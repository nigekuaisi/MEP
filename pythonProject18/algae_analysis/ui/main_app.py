import os
import glob
import traceback
import threading
import queue
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import math
import shutil
import time

# 导入自定义模块
from algae_analysis.core.formula_manager import AlgaeFormulaManager
from algae_analysis.core.data_processor import process_single_to_row, normalize_csv_format
from algae_analysis.ui.config_window import GrowthConfigWindow
from algae_analysis.ui.file_monitor import CSVFileEventHandler
from algae_analysis.config.config_manager import load_growth_config

# ================= 尝试导入 watchdog =================
try:
    from watchdog.observers import Observer
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("警告：watchdog 库未安装，自动检测功能将不可用。请运行：pip install watchdog")

# 先加载一次配置供全局使用（虽然用了依赖注入，但为了UI初始化方便）
ALGAE_GROWTH_STAGE_RULES = load_growth_config()

# ================= 主界面类 =================
class SpectralAnalysisApp:
    def __init__(self, root):
        self.root = root
        self.root.title("微藻光谱批量分析系统 v8.0 (混合藻类版)")
        self.root.geometry("1800x950")
        self.root_dir = os.getcwd()
        self.output_dir = os.getcwd()
        self.log_queue = queue.Queue()
        self.is_processing = False
        self.result_data = None
        self.temp_dir = os.path.join(os.getcwd(), "_auto_normalized_temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.auto_monitor_enabled = False
        self.observer = None
        self.processed_files_set = set()
        self.auto_result_rows = []
        self.formula_manager = AlgaeFormulaManager()
        self.formula_dict = self.formula_manager.get_formula_dict()
        self.var_concentration = tk.StringVar()
        self.var_mode = tk.StringVar(value="Single-File (Folder)")
        self.var_algae = tk.StringVar(value=list(self.formula_dict.keys())[0])
        self.var_normalize = tk.BooleanVar(value=True)
        self.create_widgets()
        self.scan_root_directory()
        self.update_log()

    def create_widgets(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)
        config_frame = ttk.LabelFrame(top_frame, text="📋 分析配置", padding=10)
        config_frame.pack(side="left", fill="both", expand=True, padx=5)
        f_root = ttk.Frame(config_frame)
        f_root.pack(fill="x", pady=3)
        ttk.Label(f_root, text="根目录:", width=8).pack(side="left")
        self.entry_root = ttk.Entry(f_root, width=45)
        self.entry_root.insert(0, self.root_dir)
        self.entry_root.pack(side="left", padx=5)
        ttk.Button(f_root, text="浏览", command=self.browse_root, width=8).pack(side="left")
        ttk.Button(f_root, text="刷新", command=self.on_root_change, width=8).pack(side="left", padx=5)
        f_output = ttk.Frame(config_frame)
        f_output.pack(fill="x", pady=3)
        ttk.Label(f_output, text="输出目录:", width=8).pack(side="left")
        self.entry_output = ttk.Entry(f_output, width=45)
        self.entry_output.insert(0, self.output_dir)
        self.entry_output.pack(side="left", padx=5)
        ttk.Button(f_output, text="浏览", command=self.browse_output, width=8).pack(side="left")
        f_conc = ttk.Frame(config_frame)
        f_conc.pack(fill="x", pady=3)
        ttk.Label(f_conc, text="浓度值:", width=8).pack(side="left")
        self.entry_conc = ttk.Entry(f_conc, width=15, textvariable=self.var_concentration)
        self.entry_conc.pack(side="left", padx=5)
        ttk.Label(f_conc, text="(可选，用于所有文件)").pack(side="left", padx=2)
        f_algae = ttk.Frame(config_frame)
        f_algae.pack(fill="x", pady=3)
        ttk.Label(f_algae, text="藻类种类:", width=8).pack(side="left")
        self.combo_algae = ttk.Combobox(
            f_algae,
            textvariable=self.var_algae,
            values=list(self.formula_dict.keys()),
            state="readonly",
            width=35,
        )
        self.combo_algae.pack(side="left", padx=5)
        ttk.Label(f_algae, text="(含混合藻类双输出)").pack(side="left", padx=2)
        ttk.Button(f_algae, text="⚙️ 配置生长期阈值", command=self.open_config_window).pack(side="left", padx=10)
        f_norm = ttk.Frame(config_frame)
        f_norm.pack(fill="x", pady=3)
        self.chk_normalize = ttk.Checkbutton(
            f_norm,
            text="✓ 启用格式标准化",
            variable=self.var_normalize,
            command=self.on_normalize_change
        )
        self.chk_normalize.pack(side="left", padx=5)
        f_mode = ttk.Frame(config_frame)
        f_mode.pack(fill="x", pady=3)
        ttk.Label(f_mode, text="分析模式:", width=8).pack(side="left")
        self.combo_mode = ttk.Combobox(
            f_mode,
            textvariable=self.var_mode,
            values=["Single-File (Folder)", "Single-File"],
            state="readonly",
            width=20,
        )
        self.combo_mode.pack(side="left", padx=5)
        self.combo_mode.bind("<<ComboboxSelected>>", self.on_mode_change)
        f_auto = ttk.Frame(config_frame)
        f_auto.pack(fill="x", pady=10)
        ttk.Label(f_auto, text="自动检测:", width=8).pack(side="left")
        self.btn_auto_toggle = ttk.Button(
            f_auto,
            text="🔴 开启自动检测",
            command=self.toggle_auto_monitor,
            width=15
        )
        self.btn_auto_toggle.pack(side="left", padx=5)
        self.lbl_auto_status = ttk.Label(
            f_auto,
            text="● 已启用" if self.auto_monitor_enabled else "○ 已禁用",
            foreground="green" if self.auto_monitor_enabled else "gray"
        )
        self.lbl_auto_status.pack(side="left", padx=5)
        if not WATCHDOG_AVAILABLE:
            self.lbl_auto_warning = ttk.Label(
                f_auto,
                text="⚠️ 需安装 watchdog: pip install watchdog",
                foreground="orange"
            )
            self.lbl_auto_warning.pack(side="left", padx=10)
        f_path = ttk.Frame(config_frame)
        f_path.pack(fill="x", pady=5)
        ttk.Label(f_path, text="路径:", width=8).pack(side="left")
        self.lbl_path = ttk.Label(
            f_path, text="等待选择...", foreground="gray", wraplength=500, justify="left"
        )
        self.lbl_path.pack(side="left", fill="x", expand=True)
        f_btn = ttk.Frame(config_frame)
        f_btn.pack(fill="x", pady=10)
        self.btn_start = ttk.Button(f_btn, text="🚀 开始分析", command=self.start_processing_thread)
        self.btn_start.pack(side="left", padx=10)
        self.btn_export = ttk.Button(
            f_btn, text="📥 导出 CSV", command=self.export_results, state="disabled"
        )
        self.btn_export.pack(side="left", padx=10)
        ttk.Button(f_btn, text="🗑️ 清理临时文件", command=self.cleanup_temp, width=15).pack(side="left", padx=10)
        ttk.Button(f_btn, text="❌ 退出", command=self.root.quit).pack(side="right", padx=10)
        result_frame = ttk.LabelFrame(self.root, text="📈 分析结果预览 (含混合藻类双输出)", padding=10)
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        tree_scroll_y = ttk.Scrollbar(result_frame, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(result_frame, orient="horizontal")
        # 新的列定义，包含双输出
        columns = (
            "Sample_ID", "Growth_Stage",
            "A430_raw", "A430_pure_abs", "A480_raw", "A480_pure_abs",
            "A680_raw", "A680_pure_abs", "A730_raw", "A730_pure_sca",
            "R_680_480", "R_abs_sca", "R_430_680", "R_680_730",
            # 微拟球藻
            "Raw_Model_Density_Nanno", "Final_Density_Nanno", "Physics_Correction_Nanno",
            # 链球藻
            "Raw_Model_Density_Chain", "Final_Density_Chain", "Physics_Correction_Chain"
        )
        self.tree = ttk.Treeview(
            result_frame,
            columns=columns,
            show="headings",
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
        )
        # 调整列宽
        col_widths = [100, 120, 75, 75, 75, 75, 75, 75, 75, 75, 80, 80, 80, 80,
                      120, 120, 150,  # Nanno
                      120, 120, 150]  # Chain
        for col, width in zip(columns, col_widths):
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c, False))
            self.tree.column(col, width=width, anchor="center")
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll_y.config(command=self.tree.yview)
        tree_scroll_y.pack(side="right", fill="y")
        tree_scroll_x.config(command=self.tree.xview)
        tree_scroll_x.pack(side="bottom", fill="x")
        log_frame = ttk.LabelFrame(self.root, text="📝 运行日志（含调试信息）", padding=5)
        log_frame.pack(fill="x", padx=10, pady=5)
        self.txt_log = tk.Text(
            log_frame, height=6, state="disabled", bg="#f5f5f5", font=("Consolas", 9)
        )
        self.txt_log.pack(fill="x", expand=True)
        sb = ttk.Scrollbar(self.txt_log, command=self.txt_log.yview)
        sb.pack(side="right", fill="y")
        self.txt_log.config(yscrollcommand=sb.set)
        self.txt_log.tag_config("INFO", foreground="black")
        self.txt_log.tag_config("SUCCESS", foreground="green")
        self.txt_log.tag_config("ERROR", foreground="red")
        self.txt_log.tag_config("WARNING", foreground="orange")
        self.txt_log.tag_config("PHYSICS", foreground="blue")
        self.txt_log.tag_config("AUTO", foreground="purple")

    def browse_output(self):
        d = filedialog.askdirectory(initialdir=self.output_dir, title="选择输出目录")
        if d:
            self.output_dir = d
            self.entry_output.delete(0, tk.END)
            self.entry_output.insert(0, d)
            self.log(f"输出目录已设置：{d}", "INFO")

    def log(self, msg, level="INFO"):
        self.log_queue.put((msg, level))

    def update_log(self):
        try:
            while True:
                msg, level = self.log_queue.get_nowait()
                self.txt_log.config(state="normal")
                ts = pd.Timestamp.now().strftime("%H:%M:%S")
                self.txt_log.insert("end", f"[{ts}] {level}: {msg}\n", level)
                self.txt_log.see("end")
                self.txt_log.config(state="disabled")
        except queue.Empty:
            pass
        self.root.after(100, self.update_log)

    def browse_root(self):
        d = filedialog.askdirectory(initialdir=self.root_dir)
        if d:
            self.root_dir = d
            self.entry_root.delete(0, tk.END)
            self.entry_root.insert(0, d)
            self.on_root_change()

    def on_root_change(self):
        self.root_dir = self.entry_root.get()
        if not os.path.isdir(self.root_dir):
            self.log("根目录无效", "ERROR")
            return
        self.scan_root_directory()
        self.log(f"根目录更新：{self.root_dir}")
        if self.auto_monitor_enabled:
            self.stop_auto_monitor()
            self.start_auto_monitor()

    def scan_root_directory(self):
        self.update_path_preview()

    def update_path_preview(self):
        p = self.root_dir
        self.lbl_path.config(text=p if p else "路径不完整", foreground="black" if p else "gray")

    def on_mode_change(self, event):
        mode = self.var_mode.get()
        if mode == "Single-File (Folder)":
            self.entry_conc.pack(side="left", padx=5)
        else:
            self.entry_conc.pack_forget()

    def on_normalize_change(self):
        if self.var_normalize.get():
            self.log("格式标准化已启用", "INFO")
        else:
            self.log("格式标准化已禁用", "WARNING")

    def cleanup_temp(self):
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                os.makedirs(self.temp_dir, exist_ok=True)
                self.log("临时文件已清理", "SUCCESS")
            except Exception as e:
                self.log(f"清理失败：{e}", "ERROR")
        else:
            self.log("无临时文件可清理", "INFO")

    def open_config_window(self):
        GrowthConfigWindow(self.root, callback=self.on_config_updated)

    def on_config_updated(self):
        global ALGAE_GROWTH_STAGE_RULES
        ALGAE_GROWTH_STAGE_RULES = load_growth_config()
        self.log("生长期阈值配置已更新", "SUCCESS")

    def toggle_auto_monitor(self):
        if not WATCHDOG_AVAILABLE:
            messagebox.showwarning("警告", "watchdog 库未安装！\n请运行：pip install watchdog\n以启用自动检测功能。")
            return
        if self.auto_monitor_enabled:
            self.stop_auto_monitor()
        else:
            self.start_auto_monitor()

    def start_auto_monitor(self):
        if not os.path.isdir(self.root_dir):
            messagebox.showerror("错误", "根目录无效，无法启动自动检测！")
            return
        try:
            existing_files = set(glob.glob(os.path.join(self.root_dir, "*.csv")))
            self.processed_files_set = existing_files.copy()
            self.log(f"已扫描 {len(self.processed_files_set)} 个现有 CSV 文件（不会重复处理）", "AUTO")
            event_handler = CSVFileEventHandler(
                callback=self.on_new_file_detected,
                processed_files_set=self.processed_files_set,
                log_callback=lambda msg, level="AUTO": self.log(msg, level)
            )
            self.observer = Observer()
            self.observer.schedule(event_handler, self.root_dir, recursive=False)
            self.observer.start()
            self.auto_monitor_enabled = True
            self.btn_auto_toggle.config(text="🟢 关闭自动检测")
            self.lbl_auto_status.config(text="● 已启用", foreground="green")
            self.log("✅ 自动检测已启动 - 新 CSV 文件将自动处理", "SUCCESS")
        except Exception as e:
            self.log(f"启动自动检测失败：{e}", "ERROR")
            messagebox.showerror("错误", f"启动自动检测失败：{e}")

    def stop_auto_monitor(self):
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=2)
                self.observer = None
            self.auto_monitor_enabled = False
            self.btn_auto_toggle.config(text="🔴 开启自动检测")
            self.lbl_auto_status.config(text="○ 已禁用", foreground="gray")
            self.log("⏹️ 自动检测已停止", "INFO")
        except Exception as e:
            self.log(f"停止自动检测失败：{e}", "ERROR")

    def on_new_file_detected(self, file_path):
        try:
            process_file = file_path
            if self.var_normalize.get():
                try:
                    temp_filename = f"_temp_{os.path.basename(file_path)}"
                    temp_path = os.path.join(self.temp_dir, temp_filename)
                    normalize_csv_format(file_path, temp_path)
                    process_file = temp_path
                    self.log(f"✓ 已标准化：{os.path.basename(file_path)}", "AUTO")
                except Exception as e:
                    self.log(f"⚠️ 标准化失败 {os.path.basename(file_path)}: {e}，尝试直接读取", "WARNING")
            conc_val = self.var_concentration.get().strip()
            if conc_val:
                try:
                    conc_val = float(conc_val)
                except ValueError:
                    conc_val = None
            else:
                conc_val = None
            selected_algae = self.var_algae.get()
            formula_func = self.formula_dict.get(selected_algae, None)
            row = process_single_to_row(
                process_file,
                conc_val,
                formula_func,
                selected_algae,
                log_callback=lambda msg, level="AUTO": self.log(msg, level)
            )
            self.auto_result_rows.append(row)
            self.root.after(0, lambda: self.add_result_row(row))
            self.root.after(0, lambda: self.log(f"✅ 处理完成：{os.path.basename(file_path)}", "SUCCESS"))
            self.root.after(0, lambda: self.save_auto_results())
            if process_file != file_path and os.path.exists(process_file):
                try:
                    os.remove(process_file)
                except:
                    pass
        except Exception as e:
            self.log(f"自动处理失败 {os.path.basename(file_path)}: {e}", "ERROR")
            traceback.print_exc()

    def add_result_row(self, row):
        values = [
            row.get("Sample_ID", ""), row.get("Growth_Stage", ""),
            row.get("A430_raw", ""), row.get("A430_pure_abs", ""),
            row.get("A480_raw", ""), row.get("A480_pure_abs", ""),
            row.get("A680_raw", ""), row.get("A680_pure_abs", ""),
            row.get("A730_raw", ""), row.get("A730_pure_sca", ""),
            row.get("R_680_480", ""), row.get("R_abs_sca", ""),
            row.get("R_430_680", ""), row.get("R_680_730", ""),
            # Nanno
            row.get("Raw_Model_Density_Nanno", ""),
            row.get("Final_Density_Nanno", ""),
            row.get("Physics_Correction_Nanno", ""),
            # Chain
            row.get("Raw_Model_Density_Chain", ""),
            row.get("Final_Density_Chain", ""),
            row.get("Physics_Correction_Chain", "")
        ]
        self.tree.insert("", "end", values=values)
        self.btn_export.config(state="normal")
        if self.result_data is not None:
            new_df = pd.DataFrame([row])
            if "Concentration" in new_df.columns:
                new_df = new_df.drop(columns=["Concentration"])
            self.result_data = pd.concat([self.result_data, new_df], ignore_index=True)
        else:
            self.result_data = pd.DataFrame([row])
            if "Concentration" in self.result_data.columns:
                self.result_data = self.result_data.drop(columns=["Concentration"])

    def save_auto_results(self):
        if not self.auto_result_rows:
            return
        try:
            selected_algae = self.var_algae.get()
            out_file = os.path.join(
                self.output_dir,
                f"spectral_auto_summary_{selected_algae.replace(' ', '_')}.xlsx"
            )
            df = pd.DataFrame(self.auto_result_rows)
            if "Concentration" in df.columns:
                df = df.drop(columns=["Concentration"])
            df.to_excel(out_file, index=False)
            self.log(f"📄 自动结果已保存：{os.path.basename(out_file)}", "SUCCESS")
        except Exception as e:
            self.log(f"保存自动结果失败：{e}", "ERROR")

    def start_processing_thread(self):
        if self.is_processing:
            messagebox.showwarning("警告", "任务正在运行中！")
            return
        root_dir = self.entry_root.get()
        if not os.path.isdir(root_dir):
            messagebox.showerror("错误", "根目录无效！")
            return
        files = glob.glob(os.path.join(root_dir, "*.csv"))
        if not files:
            messagebox.showwarning("警告", "该目录下未找到 CSV 文件")
            return
        conc_val = self.var_concentration.get().strip()
        if conc_val:
            try:
                conc_val = float(conc_val)
            except ValueError:
                messagebox.showerror("错误", "浓度值必须是数字！")
                return
        else:
            conc_val = None
        selected_algae = self.var_algae.get()
        formula_func = self.formula_dict.get(selected_algae, None)
        self.run_task(files, root_dir, conc_val, formula_func, selected_algae)

    def run_task(self, files, out_folder, conc_val, formula_func, algae_name):
        self.is_processing = True
        self.btn_start.config(state="disabled")
        self.btn_export.config(state="disabled")
        def worker():
            try:
                self.log(f"已选择藻类：{algae_name}", "INFO")
                if algae_name == "混合藻类 (微拟球藻+链球藻)":
                    self.log(f"【核心】混合藻类模式，将同时输出微拟球藻和链球藻浓度", "PHYSICS")
                else:
                    self.log(f"【核心】双参数优先判定（R_680_480 + R_abs_sca），不命中时回退单参数", "PHYSICS")
                self.log(f"【保障】100% 保留原始 MEP 模型输入，精度无损失", "SUCCESS")
                process_files = files
                if self.var_normalize.get():
                    self.log("【阶段 1/2】开始格式标准化...", "INFO")
                    self.temp_dir = os.path.join(out_folder, "_normalized_csv")
                    os.makedirs(self.temp_dir, exist_ok=True)
                    normalized_files = []
                    for i, f in enumerate(files, 1):
                        filename = os.path.basename(f)
                        dest_path = os.path.join(self.temp_dir, filename)
                        try:
                            normalize_csv_format(f, dest_path)
                            normalized_files.append(dest_path)
                            self.log(f"  [{i}/{len(files)}] ✓ {filename}", "INFO")
                        except Exception as e:
                            self.log(f"  [{i}/{len(files)}] ✗ {filename}: {e}", "ERROR")
                    process_files = normalized_files
                self.log("【阶段 2/2】开始光谱分析与物理特性提取...", "INFO")
                rows = []
                physics_warning_count = 0
                for i, f in enumerate(process_files, 1):
                    self.log(f"[{i}/{len(process_files)}] {os.path.basename(f)}", "INFO")
                    try:
                        row = process_single_to_row(f, conc_val, formula_func, algae_name, log_callback=self.log)
                        rows.append(row)
                        # 检查任一藻类的修正状态
                        if row["Physics_Correction_Nanno"] != "符合比尔 - 朗伯定律，无修正" or \
                                row["Physics_Correction_Chain"] != "符合比尔 - 朗伯定律，无修正":
                            physics_warning_count += 1
                    except Exception as e:
                        self.log(f"失败：{e}", "ERROR")
                        traceback.print_exc()
                        row = {k: None for k in
                               ["Sample_ID", "Growth_Stage", "A430_raw", "A430_pure_abs", "A480_raw", "A480_pure_abs",
                                "A680_raw", "A680_pure_abs", "A730_raw", "A730_pure_sca", "R_680_480", "R_abs_sca",
                                "R_430_680", "R_680_730",
                                "Raw_Model_Density_Nanno", "Final_Density_Nanno", "Physics_Correction_Nanno",
                                "Raw_Model_Density_Chain", "Final_Density_Chain", "Physics_Correction_Chain"]}
                        row["Sample_ID"] = os.path.splitext(os.path.basename(f))[0]
                        rows.append(row)
                df_result = pd.DataFrame(rows)
                if "Concentration" in df_result.columns:
                    df_result = df_result.drop(columns=["Concentration"])
                save_dir = self.output_dir if self.output_dir else out_folder
                out_file = os.path.join(save_dir, f"spectral_batch_summary_{algae_name.replace(' ', '_')}.xlsx")
                df_result.to_excel(out_file, index=False)
                self.root.after(0, lambda: self.update_results_display(df_result, out_file))
                self.log(f"处理完成！共{len(rows)}个样本，{physics_warning_count}个样本触发物理约束修正", "SUCCESS")
                self.log(f"结果已保存至：{out_file}", "SUCCESS")
            except Exception as e:
                self.log(f"严重错误：{e}", "ERROR")
                traceback.print_exc()
            finally:
                self.root.after(0, lambda: self.btn_start.config(state="normal"))
                self.is_processing = False
        threading.Thread(target=worker, daemon=True).start()

    def update_results_display(self, df, out_file):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.result_data = df
        self.out_file_path = out_file
        for _, row in df.iterrows():
            values = [
                row.get("Sample_ID", ""), row.get("Growth_Stage", ""),
                row.get("A430_raw", ""), row.get("A430_pure_abs", ""),
                row.get("A480_raw", ""), row.get("A480_pure_abs", ""),
                row.get("A680_raw", ""), row.get("A680_pure_abs", ""),
                row.get("A730_raw", ""), row.get("A730_pure_sca", ""),
                row.get("R_680_480", ""), row.get("R_abs_sca", ""),
                row.get("R_430_680", ""), row.get("R_680_730", ""),
                row.get("Raw_Model_Density_Nanno", ""),
                row.get("Final_Density_Nanno", ""),
                row.get("Physics_Correction_Nanno", ""),
                row.get("Raw_Model_Density_Chain", ""),
                row.get("Final_Density_Chain", ""),
                row.get("Physics_Correction_Chain", "")
            ]
            self.tree.insert("", "end", values=values)
        self.btn_export.config(state="normal")

    def sort_treeview(self, col, reverse):
        if self.result_data is None:
            return
        data = [(self.tree.set(child, col), child) for child in self.tree.get_children("")]
        try:
            data.sort(key=lambda x: float(x[0]) if x[0] else 0, reverse=reverse)
        except:
            data.sort(key=lambda x: x[0], reverse=reverse)
        for idx, (val, child) in enumerate(data):
            self.tree.move(child, "", idx)
        self.tree.heading(col, command=lambda c=col: self.sort_treeview(c, not reverse))

    def export_results(self):
        if self.result_data is None:
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv"), ("Excel 文件", "*.xlsx")],
            initialfile=f"spectral_results_{self.var_algae.get().replace(' ', '_')}.csv"
        )
        if file_path:
            if file_path.endswith(".xlsx"):
                self.result_data.to_excel(file_path, index=False)
            else:
                self.result_data.to_csv(file_path, index=False, encoding="utf-8-sig")
            self.log(f"数据已导出至：{file_path}", "SUCCESS")

    def on_closing(self):
        if self.auto_monitor_enabled:
            self.stop_auto_monitor()
        self.cleanup_temp()
        self.root.destroy()