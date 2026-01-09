import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QLabel, QSlider, 
                             QMenu, QSystemTrayIcon, QStyle, QFrame)
from PyQt6.QtCore import Qt, QTimer, QTime, QSize
from PyQt6.QtGui import QIcon, QAction, QFont, QPalette, QColor, QResizeEvent, QPainter, QPen
import winsound

class ReloadIcon(QIcon):
    def __init__(self):
        super().__init__()
        self.addPixmap(self.create_icon())
        
    def create_icon(self):
        from PyQt6.QtGui import QPixmap, QPainter, QPen, QColor
        from PyQt6.QtCore import QPointF
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)
        
        center_x = 16
        center_y = 16
        radius = 10
        
        painter.drawArc(center_x - radius, center_y - radius, radius * 2, radius * 2, 0, 180 * 16)
        
        arrow_size = 5
        
        painter.drawLine(center_x + radius, center_y, center_x + radius - arrow_size, center_y - arrow_size)
        painter.drawLine(center_x + radius, center_y, center_x + radius - arrow_size, center_y + arrow_size)
        
        painter.drawArc(center_x - radius, center_y - radius, radius * 2, radius * 2, 180 * 16, 180 * 16)
        
        painter.drawLine(center_x - radius, center_y, center_x - radius + arrow_size, center_y - arrow_size)
        painter.drawLine(center_x - radius, center_y, center_x - radius + arrow_size, center_y + arrow_size)
        
        painter.end()
        
        return pixmap

class TimerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.elapsed_time = 0
        self.is_running = False
        self.target_hours = 0
        self.target_minutes = 0
        self.target_set = False
        self.alert_triggered = False
        self.last_window_width = 0
        self.last_window_height = 0
        
        self.init_ui()
        self.init_timer()
        self.init_system_tray()
        
    def init_ui(self):
        self.setWindowTitle('桌面计时器')
        self.setMinimumSize(150, 150)
        self.resize(300, 200)
        
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        
        self.setWindowOpacity(0.75)
        
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.setStyleSheet("""
            QMainWindow {
                background-color: rgba(128, 128, 128, 180);
            }
            QPushButton {
                background-color: white;
                color: #333;
                border: none;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
            }
            QPushButton:pressed {
                background-color: #e8e8e8;
            }
            QPushButton#iconButton {
                background-color: white;
                border: none;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton#iconButton:hover {
                background-color: #f5f5f5;
            }
            QPushButton#iconButton:pressed {
                background-color: #e8e8e8;
            }
            QLabel {
                color: white;
                font-weight: 300;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 0;
            }
            QSlider::handle:horizontal {
                background: white;
                width: 16px;
                margin: -6px 0;
                border-radius: 0;
            }
            QMenu {
                background-color: rgba(64, 64, 64, 240);
                color: white;
                border: none;
            }
            QMenu::item {
                padding: 10px 20px;
            }
            QMenu::item:selected {
                background-color: rgba(100, 100, 100, 240);
            }
        """)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        
        main_layout.addStretch(1)
        
        self.time_label = QLabel('00:00:00.000')
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.time_label)
        
        main_layout.addStretch(1)
        
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton()
        self.start_button.setObjectName('iconButton')
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.clicked.connect(self.start_timer)
        button_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton()
        self.pause_button.setObjectName('iconButton')
        self.pause_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
        self.pause_button.clicked.connect(self.pause_timer)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)
        
        self.reset_button = QPushButton()
        self.reset_button.setObjectName('iconButton')
        self.reset_button.setIcon(ReloadIcon())
        self.reset_button.clicked.connect(self.reset_timer)
        button_layout.addWidget(self.reset_button)
        
        main_layout.addLayout(button_layout)
        
        transparency_layout = QHBoxLayout()
        transparency_label = QLabel('透明度:')
        transparency_label.setStyleSheet('color: white; font-size: 12px;')
        transparency_layout.addWidget(transparency_label)
        
        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setRange(10, 100)
        self.transparency_slider.setValue(50)
        self.transparency_slider.valueChanged.connect(self.set_transparency)
        transparency_layout.addWidget(self.transparency_slider)
        
        main_layout.addLayout(transparency_layout)
        
        central_widget.setLayout(main_layout)
        
        self.create_title_bar_buttons()
        
        self.adjust_font_sizes()
        
    def create_title_bar_buttons(self):
        title_bar = QWidget(self)
        title_bar.setGeometry(self.width() - 120, 5, 115, 30)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(5)
        
        self.pin_button = QPushButton('📌')
        self.pin_button.setFixedSize(30, 30)
        self.pin_button.clicked.connect(self.toggle_pin)
        self.pin_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        self.minimize_button = QPushButton('−')
        self.minimize_button.setFixedSize(30, 30)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.minimize_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        self.close_button = QPushButton('×')
        self.close_button.setFixedSize(30, 30)
        self.close_button.clicked.connect(self.close)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 24px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.5);
            }
        """)
        
        title_layout.addWidget(self.pin_button)
        title_layout.addWidget(self.minimize_button)
        title_layout.addWidget(self.close_button)
        
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.adjust_font_sizes()
        
    def adjust_font_sizes(self):
        window_height = self.height()
        window_width = self.width()
        
        width_changed = window_width != self.last_window_width
        height_changed = window_height != self.last_window_height
        
        if self.last_window_width != 0 and self.last_window_height != 0 and not (width_changed and height_changed):
            return
        
        self.last_window_width = window_width
        self.last_window_height = window_height
        
        time_font_size_by_width = max(12, int(window_width * 0.16))
        time_font_size_by_height = max(12, int(window_height * 0.16))
        time_font_size = min(time_font_size_by_width, time_font_size_by_height)
        button_font_size = max(10, int(window_height * 0.06))
        
        time_font = QFont('Arial', time_font_size, QFont.Weight.Bold)
        self.time_label.setFont(time_font)
        
        button_font = QFont('Arial', button_font_size, QFont.Weight.Normal)
        self.start_button.setFont(button_font)
        self.pause_button.setFont(button_font)
        self.reset_button.setFont(button_font)
        
    def init_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.setInterval(10)
        
    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon))
        
        tray_menu = QMenu()
        
        sound_action = QAction('声音提醒设置', self)
        sound_action.triggered.connect(self.show_sound_settings_dialog)
        tray_menu.addAction(sound_action)
        
        restore_action = QAction('恢复', self)
        restore_action.triggered.connect(self.showNormal)
        tray_menu.addAction(restore_action)
        
        quit_action = QAction('退出', self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()
        
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.showNormal()
            self.activateWindow()
            
    def set_transparency(self, value):
        opacity = value / 100.0
        self.setWindowOpacity(opacity)
        
    def show_sound_settings_dialog(self):
        dialog = QWidget(self)
        dialog.setWindowTitle('声音提醒设置')
        dialog.setFixedSize(350, 250)
        dialog.setStyleSheet("""
            QWidget {
                background-color: rgba(64, 64, 64, 240);
                color: white;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QPushButton {
                background-color: white;
                color: black;
                border: 2px solid #ccc;
                border-radius: 5px;
                padding: 5px 15px;
            }
        """)
        
        layout = QVBoxLayout(dialog)
        
        hours_label = QLabel(f'目标时间: {self.target_hours} 小时 {self.target_minutes} 分钟')
        layout.addWidget(hours_label)
        
        hours_slider = QSlider(Qt.Orientation.Horizontal)
        hours_slider.setRange(0, 99)
        hours_slider.setValue(self.target_hours)
        hours_slider.valueChanged.connect(lambda v: hours_label.setText(f'目标时间: {v} 小时 {self.target_minutes} 分钟'))
        hours_slider.valueChanged.connect(lambda v: self.set_target_hours(v))
        layout.addWidget(hours_slider)
        
        minutes_slider = QSlider(Qt.Orientation.Horizontal)
        minutes_slider.setRange(0, 11)
        minutes_slider.setValue(self.target_minutes // 5)
        minutes_slider.valueChanged.connect(lambda v: hours_label.setText(f'目标时间: {self.target_hours} 小时 {v * 5} 分钟'))
        minutes_slider.valueChanged.connect(lambda v: self.set_target_minutes(v * 5))
        layout.addWidget(minutes_slider)
        
        ok_button = QPushButton('确定')
        ok_button.clicked.connect(dialog.close)
        ok_button.clicked.connect(self.enable_alert)
        layout.addWidget(ok_button)
        
        dialog.show()
        
    def set_target_hours(self, hours):
        self.target_hours = hours
        
    def set_target_minutes(self, minutes):
        self.target_minutes = minutes
        
    def enable_alert(self):
        self.target_set = True
        self.alert_triggered = False
        
    def start_timer(self):
        self.is_running = True
        self.timer.start()
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        
    def pause_timer(self):
        self.is_running = False
        self.timer.stop()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        
    def reset_timer(self):
        self.is_running = False
        self.timer.stop()
        self.elapsed_time = 0
        self.alert_triggered = False
        self.update_display()
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        
    def update_time(self):
        if self.is_running:
            self.elapsed_time += 10
            self.update_display()
            self.check_alert()
            
    def update_display(self):
        hours = self.elapsed_time // 3600000
        minutes = (self.elapsed_time % 3600000) // 60000
        seconds = (self.elapsed_time % 60000) // 1000
        milliseconds = self.elapsed_time % 1000
        
        time_str = f'{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}'
        self.time_label.setText(time_str)
        
    def check_alert(self):
        if self.target_set and not self.alert_triggered:
            target_ms = self.target_hours * 3600000 + self.target_minutes * 60000
            if self.elapsed_time >= target_ms:
                self.play_alert()
                self.alert_triggered = True
                
    def play_alert(self):
        sound_file = os.path.join(os.path.dirname(__file__), 'notification_sound.wav')
        if os.path.exists(sound_file):
            winsound.PlaySound(sound_file, winsound.SND_FILENAME)
        else:
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
            
    def toggle_pin(self):
        flags = self.windowFlags()
        if flags & Qt.WindowType.WindowStaysOnTopHint:
            self.setWindowFlags(flags & ~Qt.WindowType.WindowStaysOnTopHint)
            self.pin_button.setText('📌')
        else:
            self.setWindowFlags(flags | Qt.WindowType.WindowStaysOnTopHint)
            self.pin_button.setText('📍')
        self.show()
        
    def closeEvent(self, event):
        self.tray_icon.hide()
        event.accept()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    timer_app = TimerApp()
    timer_app.show()
    
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
