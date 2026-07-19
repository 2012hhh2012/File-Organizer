from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QTableWidgetItem
from PyQt6.QtGui import QIcon
from PyQt6 import uic
import sys
import json
import hashlib
import os

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)

        self.user_manager = UserManager()
        self.show_signin()

        self.setWindowIcon(QIcon("file-organizer-logo.svg"))

        self.btn_signin.clicked.connect(self.handel_signin)
        self.btn_go_signup.clicked.connect(self.show_signup)
        self.btn_signup.clicked.connect(self.handel_signup)
        self.btn_go_signin.clicked.connect(self.show_signin)

        self.btn_nav_dash.clicked.connect(lambda: self.show_app_page(0))
        self.btn_nav_rules.clicked.connect(lambda: self.show_app_page(1))
        self.btn_nav_tasks.clicked.connect(lambda: self.show_app_page(2))
        self.btn_nav_archive.clicked.connect(lambda: self.show_app_page(3))
        self.btn_nav_settings.clicked.connect(lambda: self.show_app_page(4))

        self.btn_signout.clicked.connect(self.handel_signout)

        self.btn_browse_folder.clicked.connect(self.browse_folder)
        self.btn_run_cleanup.clicked.connect(self.run_cleanup)

        self.btn_add_rule.clicked.connect(lambda: self.add_rule(ext_obj = self.txt_new_ext, dest_obj = self.txt_new_dest))
        self.btn_remove_rule.clicked.connect(lambda: self.remove_rule(table_obj = self.table_rules))

        self.btn_add_rule_full.clicked.connect(lambda: self.add_rule(ext_obj = self.txt_rule_ext, dest_obj = self.txt_rule_dest))
        self.btn_remove_rule_full.clicked.connect(lambda: self.remove_rule(table_obj = self.table_rules_full))

        self.table_rules.cellChanged.connect(self.on_cell_changed)
        self.table_rules_full.cellChanged.connect(self.on_cell_changed)

    def load_user(self):
        # Display username
        self.lbl_sidebar_username.setText(f"Username: {self.user_manager.current_user["username"]}")

        # Load rules tables
        self.table_rules.blockSignals(True) # Block change signals
        self.table_rules_full.blockSignals(True)

        self.table_rules.setRowCount(0)
        self.table_rules_full.setRowCount(0)

        rules = self.user_manager.current_user["rules"]

        for folder, exts in rules.items():
            row = self.table_rules.rowCount()

            self.table_rules.insertRow(row)
            self.table_rules_full.insertRow(row)

            ext_string = ", ".join(exts)

            self.table_rules.setItem(row, 0, QTableWidgetItem(ext_string))
            self.table_rules.setItem(row, 1, QTableWidgetItem(folder))
            self.table_rules_full.setItem(row, 0, QTableWidgetItem(ext_string))
            self.table_rules_full.setItem(row, 1, QTableWidgetItem(folder))

        self.table_rules.resizeColumnsToContents()
        self.table_rules_full.resizeColumnsToContents()

        self.table_rules.verticalHeader().setDefaultSectionSize(40)
        self.table_rules_full.verticalHeader().setDefaultSectionSize(40)

        self.table_rules.blockSignals(False)
        self.table_rules_full.blockSignals(False)

        # Activity log
        self.txt_activity_log.setPlainText("> Rules table loaded\n> Session active. Awaiting instruction...")

    def on_cell_changed(self, row, column):
        if not row and not column:
            return
        exts = self.table_rules.item(row, 0)
        dest = self.table_rules.item(row, 1)

        extension_list = [ext.strip() for ext in exts.text().split(",") if ext.strip()]
        for i in range(len(extension_list)):
            if not extension_list[i].startswith("."):
                extension_list[i] = "." + extension_list[i]

        exts = ", ".join(extension_list)
        
        self.user_manager.edit_rule(row, extension_list, dest.text())
        
        self.txt_activity_log.appendPlainText(f"> Rule edited: {exts}: {dest.text()}")
    
    def add_rule(self, ext_obj, dest_obj):
        self.table_rules.blockSignals(True)
        self.table_rules_full.blockSignals(True)

        row = self.table_rules.rowCount()
        exts = ext_obj.text()
        dest = dest_obj.text()

        extension_list = [ext.strip() for ext in exts.split(",") if ext.strip()]
        for i in range(len(extension_list)):
            if not extension_list[i].startswith("."):
                extension_list[i] = "." + extension_list[i]

        exts = ", ".join(extension_list)

        self.user_manager.add_rule(extension_list, dest)

        ext_obj.clear()
        dest_obj.clear()

        self.table_rules.insertRow(row)
        self.table_rules_full.insertRow(row)

        self.table_rules.setItem(row, 0, QTableWidgetItem(exts))
        self.table_rules.setItem(row, 1, QTableWidgetItem(dest))
        self.table_rules_full.setItem(row, 0, QTableWidgetItem(exts))
        self.table_rules_full.setItem(row, 1, QTableWidgetItem(dest))

        self.table_rules.blockSignals(False)
        self.table_rules_full.blockSignals(False)

        self.txt_activity_log.appendPlainText(f"> Rule added: {exts}: {dest}")

    def remove_rule(self, table_obj):
        row = table_obj.currentRow()

        if row < 1:
            QMessageBox.critical(self, "Error", "Please select a rule to remove")
            return
        
        dest = table_obj.item(row, 1).text()

        self.user_manager.remove_rule(dest)

        self.table_rules.removeRow(row)
        self.table_rules_full.removeRow(row)

        self.txt_activity_log.appendPlainText(f"> Rule removed: {dest}")

    def calculate_file_hash(self, filepath, chunk_size=8192):
        """Generates an SHA-256 hash for a file in a memory-efficient way."""
        hasher = hashlib.sha256()
        with open(filepath, 'rb') as f:  # Always open in binary mode
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def run_cleanup(self):
        self.txt_activity_log.appendPlainText("> Cleanup started")

        moved = 0
        purged = 0

        path = self.line_target_folder.text()
        if not os.path.exists(path):
            self.txt_activity_log.appendPlainText("> Cleanup failed: Target folder does not exist")
            QMessageBox.critical(self, "Error", "Target folder does not exist")
            return
        remove_duplicate = self.chk_dedup.isChecked()
        file_hashes = []
        for filename in os.listdir(path):
            root, ext = os.path.splitext(filename)
            filepath = os.path.join(path, filename)
            if os.path.isfile(filepath):
                if remove_duplicate:
                    file_hash = self.calculate_file_hash(filepath)
                    if file_hash in file_hashes:
                        os.remove(filepath)
                        purged += 1
                        print(f"Duplicate file {filename} found and removed: {filepath}")
                        self.txt_activity_log.appendPlainText(f'> Duplicate file "{filename}" found and removed')
                        continue

                file_hashes.append(file_hash)
                destination = self.user_manager.get_directory(ext)

                if destination:
                    if not os.path.exists(os.path.join(path, destination)):
                        os.makedirs(os.path.join(path, destination))
                    os.rename(filepath, os.path.join(path, destination, filename))
                    moved += 1
                    print(f"File {filename} moved to {destination}")
                    self.txt_activity_log.appendPlainText(f'> File "{filename}" moved to {destination}')

        self.txt_activity_log.appendPlainText(f"> Cleanup completed, {moved} files moved and {purged} duplicates removed")
        QMessageBox.information(self, "Success", "Cleanup completed successfully")

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory",  # Dialog title
            "",  # Starting directory (empty = default)
            QFileDialog.Option.ShowDirsOnly  # Only show directories
        )
        
        if folder:
            self.line_target_folder.setText(folder)
            self.txt_activity_log.appendPlainText(f"> Target folder set to: {folder}")

    def handel_signin(self):
        email = self.txt_signin_email.text()
        password = self.txt_signin_password.text()
        if not email or not password:
            QMessageBox.critical(self, "Error", "Please enter email and password")
            return
        status = self.user_manager.sign_in(email, password)
        if status:
            self.txt_signin_email.clear()
            self.txt_signin_password.clear()
            QMessageBox.information(self, "Success", "Login successful")
            self.load_user()
            self.show_app_page(0)
        else:
            self.txt_signin_email.clear()
            self.txt_signin_password.clear()
            QMessageBox.critical(self, "Error", "Incorrect email or password")

    def handel_signup(self):
        email = self.txt_signup_email.text()
        username = self.txt_signup_username.text()
        password = self.txt_signup_password.text()
        if not email or not username or not password:
            QMessageBox.critical(self, "Error", "Please enter email, username, and password")
            return
        status = self.user_manager.sign_up(email, username, password)
        if status:
            self.txt_signup_email.clear()
            self.txt_signup_username.clear()
            self.txt_signup_password.clear()
            QMessageBox.information(self, "Success", "Registration successful")
            self.load_user()
            self.show_app_page(0)

    def handel_signout(self):
        self.user_manager.signout()
        self.stackedWidget_main.setCurrentIndex(0)

    def show_app_page(self, index):
        self.stackedWidget_main.setCurrentIndex(2)
        self.stackedWidget_app.setCurrentIndex(index)

    def show_signin(self):
        self.txt_signin_email.clear()
        self.txt_signin_password.clear()
        self.stackedWidget_main.setCurrentIndex(0)

    def show_signup(self):
        self.txt_signup_email.clear()
        self.txt_signup_username.clear()
        self.txt_signup_password.clear()
        self.stackedWidget_main.setCurrentIndex(1)

    # pages order:
    # - stackedWidget_main
    #   - 0: signin
    #   - 1: signup
    #   - 2: main_app
    #     - stackedWidget_app
    #       - 0: dashboard_view
    #       - 1: rules_view
    #       - 2: tasks_view      
    #       - 3: archive_view
    #       - 4: settings_view

class UserManager:
    def __init__(self):
        self.users = self.read_json()
        self.current_user = None
        self.current_rules = {}

    def parse_rules(self):
        self.current_rules = {}
        if self.current_user:
            rules = self.current_user["rules"]
            for folder, extensions in rules.items():
                for ext in extensions:
                    self.current_rules[ext] = folder

    def get_directory(self, ext):
        return self.current_rules.get(ext, None)

    def edit_rule(self, row, new_exts: list[str], new_dest):
        old_dest = list(self.current_user["rules"].keys())[row]
        
        self.current_user["rules"][new_dest] = new_exts
        if not old_dest == new_dest:
            self.remove_rule(old_dest)
    
    def add_rule(self, exts: list[str], dest):
        self.current_user["rules"][dest] = exts
        self.parse_rules()
        self.save_json(self.users)

    def remove_rule(self, dest):
        del self.current_user["rules"][dest]
        self.parse_rules()
        self.save_json(self.users)

    def sign_up(self, email, username, password):
        for user in self.users:
            if user["email"] == email:
                self.txt_signup_email.clear()
                QMessageBox.critical(self, "Error", "Email already exists")
                return False
            
            elif user["username"] == username:
                self.txt_signup_username.clear()
                QMessageBox.critical(self, "Error", "Username already exists")
                return False
            
        new_user = {
            "email": email,
            "username": username,
            "password": password,
            "rules_preset": "Documents", # Default preset
            "rules": {
                "Documents": [".pdf", ".docx", ".txt", ".rtf", ".odt"],
                "Images": [".jpg", ".png", ".gif", ".bmp", ".svg"],
                "Videos": [".mp4", ".mov", ".avi", ".mkv"],
                "Music": [".mp3", ".wav", ".flac", ".aac"],
                "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
                "Installers": [".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm"],
                "Disk Images": [".iso", ".img", ".bin"],
                "Torrents": [".torrent"],
                "Scripts": [".bat", ".sh", ".ps1", ".py", ".js"],
                "Spreadsheets": [".xlsx", ".xls", ".csv"],
                "Presentations": [".pptx", ".ppt", ".odp"],
                "Code": [".py", ".js", ".html", ".css", ".cpp", ".java"],
                "Text": [".txt", ".log", ".md"],
                "Fonts": [".ttf", ".otf"],
                "Databases": [".db", ".sqlite", ".sql"]
            }
        }
        self.users.append(new_user)
        self.current_user = new_user
        self.parse_rules()
        self.save_json(self.users)
        return True

    def sign_in(self, email, password):
        for user in self.users:
            if user["email"] == email and user["password"] == password:
                self.current_user = user
                self.parse_rules()
                return True
        else:
            return False

    def save_json(self, data):
        with open("data.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def read_json(self):
        with open("data.json", "r", encoding="utf-8") as file:
            return json.load(file)

    def signout(self):
        self.current_user = None
        self.current_rules = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()