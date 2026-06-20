from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from PyQt6 import uic
import sys
import json

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main.ui", self)
        self.data = self.read_json()
        self.current_user = None
        self.btn_signin.clicked.connect(self.handel_signin)
        self.btn_go_signup.clicked.connect(self.show_signup)
        self.btn_signup.clicked.connect(self.handel_signup)
        self.btn_go_signin.clicked.connect(self.show_signin)

    def handel_signin(self):
        email = self.txt_signin_email.text()
        password = self.txt_signin_password.text()
        for user in self.data:
            if user["email"] == email and user["password"] == password:
                self.txt_signin_email.clear()
                self.txt_signin_password.clear()
                QMessageBox.information(self, "Success", "Login successful")
                self.stackedWidget.setCurrentIndex(2)
                self.current_user = user
                break
        else:
            self.txt_signin_email.clear()
            self.txt_signin_password.clear()
            QMessageBox.critical(self, "Error", "Incorrect email or password")

    def handel_signup(self):
        email = self.txt_signup_email.text()
        username = self.txt_signup_username.text()
        password = self.txt_signup_password.text()
        for user in self.data:
            if user["email"] == email:
                self.txt_signup_email.clear()
                QMessageBox.critical(self, "Error", "Email already exists")
                return
            elif user["username"] == username:
                self.txt_signup_username.clear()
                QMessageBox.critical(self, "Error", "Username already exists")
                return
        new_user = {
            "email": email,
            "username": username,
            "password": password
        }
        self.data.append(new_user)
        self.save_json(self.data)
        self.txt_signup_email.clear()
        self.txt_signup_username.clear()
        self.txt_signup_password.clear()
        QMessageBox.information(self, "Success", "Registration successful")
        self.stackedWidget.setCurrentIndex(2)
        self.current_user = new_user

    def show_signin(self):
        self.txt_signin_email.clear()
        self.txt_signin_password.clear()
        self.stackedWidget.setCurrentIndex(0)

    def show_signup(self):
        self.txt_signup_email.clear()
        self.txt_signup_username.clear()
        self.txt_signup_password.clear()
        self.stackedWidget.setCurrentIndex(1)

    def save_json(self, data):
        with open("data.json", "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def read_json(self):
        with open("data.json", "r", encoding="utf-8") as file:
            return json.load(file)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()