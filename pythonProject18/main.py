import sys
import os
import tkinter as tk

# ================= 添加项目根目录到Python路径 =================
# 获取当前文件(main.py)的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 将项目根目录添加到Python模块搜索路径
sys.path.insert(0, current_dir)

# ================= 导入应用程序模块 =================
from algae_analysis.ui.main_app import SpectralAnalysisApp

# ================= 程序入口 =================
if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = SpectralAnalysisApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()