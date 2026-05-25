import threading
import os
# ================= 尝试导入 watchdog =================
try:
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    FileSystemEventHandler = object # 定义一个占位符防止类定义报错


class CSVFileEventHandler(FileSystemEventHandler):
    def __init__(self, callback, processed_files_set, log_callback):
        super().__init__()
        self.callback = callback
        self.processed_files = processed_files_set
        self.log_callback = log_callback
        self.pending_files = {}
        self.lock = threading.Lock()
        self.DEBOUNCE_SECONDS = 2.0

    def _schedule_processing(self, file_path):
        with self.lock:
            if file_path in self.pending_files:
                self.pending_files[file_path].cancel()
            timer = threading.Timer(self.DEBOUNCE_SECONDS, self._process_file, args=[file_path])
            self.pending_files[file_path] = timer
            timer.start()

    def _process_file(self, file_path):
        with self.lock:
            if file_path in self.pending_files:
                del self.pending_files[file_path]
            if file_path in self.processed_files:
                return
            if not os.path.exists(file_path) or not file_path.lower().endswith('.csv'):
                return
            self.processed_files.add(file_path)
        if self.callback:
            self.callback(file_path)
        if self.log_callback:
            self.log_callback(f"📁 检测到新文件：{os.path.basename(file_path)}", "INFO")

    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith('.csv'):
            self._schedule_processing(event.src_path)

    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.lower().endswith('.csv'):
            self._schedule_processing(event.src_path)