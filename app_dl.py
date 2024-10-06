import sys
import requests
from PyQt6 import QtWidgets, QtCore
from tqdm import tqdm
import threading
import time


class DownloadThread(QtCore.QThread):
    progress = QtCore.pyqtSignal(int)
    finished = QtCore.pyqtSignal()

    def __init__(self, url, limit_speed=None):
        super().__init__()
        self.url = url
        self.limit_speed = limit_speed
        print('start')

    def run(self):
        response = requests.head(self.url)
        file_size = int(response.headers.get('content-length', 0))

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

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Downloader')
        self.setGeometry(100, 100, 400, 200)

        self.url_label = QtWidgets.QLabel('URL:')
        self.url_input = QtWidgets.QLineEdit(self)
        self.url_input.setPlaceholderText("https://example.com/files/example.exe")

        self.speed_label = QtWidgets.QLabel('Max Speed (MB/sec):')
        self.speed_input = QtWidgets.QSpinBox(self)
        self.speed_input.setValue(5)

        self.download_button = QtWidgets.QPushButton('Download', self)
        self.download_button.clicked.connect(self.start_download)

        self.progress_bar = QtWidgets.QProgressBar(self)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.speed_label)
        layout.addWidget(self.speed_input)
        layout.addWidget(self.download_button)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def start_download(self):
        url = self.url_input.text()
        limit_speed = self.speed_input.text()

        limit_speed = int(limit_speed) if limit_speed.isdigit() else None

        self.download_thread = DownloadThread(url, (limit_speed*1024)*1024)
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)

        self.download_thread.start()

    def update_progress(self, bytes_downloaded):
        self.progress_bar.setValue(self.progress_bar.value() + bytes_downloaded)

    def download_finished(self):
        QtWidgets.QMessageBox.warning(self, 'Finished', 'Download finished!')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    downloader = DownloadApp()
    downloader.show()
    sys.exit(app.exec())
