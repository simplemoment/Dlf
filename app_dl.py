from PyQt6 import QtWidgets, QtCore, QtGui
from tqdm import tqdm
import sys, requests, time, os

def rload(filepath):
    if hasattr(sys, "_MEIPASS"): return os.path.join(sys._MEIPASS, filepath)
    else: return os.path.join(os.path.abspath("."), filepath)

kb = 1024
mb = kb*kb

class Variable:
    def __init__(self, dif_value):
        self.value = dif_value
    def setValue(self, value):
        self.value = value
    def getValue(self):
        return self.value

class DownloadThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, url, progbar, progbar_line, totalfs, limit_speed=None):
        super().__init__()
        self.url = url
        self.progbar = progbar
        self.progbar_line = progbar_line
        self.totalfs = totalfs
        self.limit_speed = limit_speed

    def run(self):
        response = requests.head(self.url)
        file_size = int(response.headers.get('content-length', 0))
        self.totalfs.setValue(int(file_size))
        self.progbar_line.setText("0/0 MB")
        self.progbar.setValue(0)
        self.progbar.setMaximum(int(file_size))

        response = requests.get(self.url, stream=True)
        filename = self.url.split('/')[-1]

        with open(filename, 'wb') as file:
            progress_bar = tqdm(total=file_size, unit='B', unit_scale=True)

            for data in response.iter_content(chunk_size=1024):
                file.write(data)
                self.progress.emit(len(data))
                progress_bar.update(len(data))

                if self.limit_speed:
                    time.sleep(len(data) / self.limit_speed)

            progress_bar.close()
        self.finished.emit()


class DownloadApp(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        self.download_thread = ""
        self.total_fs = Variable(0)

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('DLF')
        self.setWindowIcon(QtGui.QIcon(rload('app.ico')))
        self.setGeometry(100, 100, 400, 200)

        self.url_label = QtWidgets.QLabel('URL:')
        self.url_input = QtWidgets.QLineEdit(self)
        self.url_input.setPlaceholderText("https://example.com/files/example.exe")

        self.open_dl_path_button = QtWidgets.QPushButton(self)
        self.open_dl_path_button.setText("Open folder")
        self.open_dl_path_button.clicked.connect(self.open_dl_path)

        self.speed_label = QtWidgets.QLabel('Max Speed (MB/sec):')
        self.speed_input = QtWidgets.QSpinBox(self)
        self.speed_input.setValue(5)

        self.download_button = QtWidgets.QPushButton('Start dl', self)
        self.download_button.clicked.connect(self.start_download)

        self.progress_bar = QtWidgets.QProgressBar(self)
        self.progress_bottom_label = QtWidgets.QLabel(self)
        self.progress_bottom_label.setText("0/0 MB")

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.speed_label)
        layout.addWidget(self.speed_input)
        layout.addWidget(self.download_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_bottom_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)

    def start_download(self):
        url = self.url_input.text()
        limit_speed = self.speed_input.text()

        limit_speed = int(limit_speed) if limit_speed.isdigit() else None

        self.download_thread = DownloadThread(url, self.progress_bar, self.progress_bottom_label, self.total_fs, (limit_speed*1024)*1024)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)

        if url == "" or not "http" in url:QtWidgets.QMessageBox.warning(self, self.windowTitle(), "Enter url!!!")
        else:self.download_thread.start()

    def update_progress(self, bytes_downloaded):
        self.progress_bar.setValue(self.progress_bar.value() + bytes_downloaded)
        self.progress_bottom_label.setText(f"{round((self.progress_bar.value()+bytes_downloaded)/mb, 2)}/{round(self.total_fs.getValue()/mb, 2)} MB")

    def download_finished(self):
        self.progress_bar.setValue(self.progress_bar.value()+1)
        self.progress_bottom_label.setText(f"{round((self.progress_bar.value()+1)/mb, 2)}/{round(self.total_fs.getValue()/mb, 2)} MB")
        QtWidgets.QMessageBox.information(self, self.windowTitle(), 'Download finished!')

    def open_dl_path(self):
        os.system(r'explorer "."')
# END
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    downloader = DownloadApp()
    downloader.show()
    sys.exit(app.exec())
