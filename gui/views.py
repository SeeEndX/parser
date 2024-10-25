import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox as mb
from parser_logic import logic
import queue
import threading

class ToplevelWindow(ctk.CTkToplevel):
    def __init__(self, master, text):
        super().__init__(master)
        self.geometry("200x150")
        self.label = ctk.CTkLabel(self, text=text)
        self.label.pack(padx=20, pady=20)  

class CheckboxFrame(ctk.CTkFrame):
    def __init__(self, master, title, values, app_instance):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.title = title

        self.checkboxes = []
        self.app_instance = app_instance

        self.title = ctk.CTkLabel(self, text=self.title, fg_color="LightSlateGray", text_color="white", corner_radius=6, font=ctk.CTkFont(size=18))
        self.title.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="ew")

        for i, value in enumerate(self.values):
            checkbox = ctk.CTkCheckBox(self, text=value, font=ctk.CTkFont(size=14))
            checkbox.grid(row=i+1, column=0, padx=10, pady=(10, 0), sticky="w")
            self.checkboxes.append(checkbox)
        
        self.apply_button = ctk.CTkButton(self, text="Применить настройки", command=self.app_instance.apply_button_callbck, font=ctk.CTkFont(size=14), text_color="Black", fg_color="White", hover_color="DarkGray",)
        self.apply_button.grid(row=5, column=0, padx=10, pady=(155,0))

    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
        return checked_checkboxes
    
class ButtonFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.app_instance = app_instance

        self.start_button = ctk.CTkButton(self, text="Начать", command=self.app_instance.start_button_callbck,font=ctk.CTkFont(size=16))
        self.start_button.grid(row=0, column=0, padx=10, pady=10)
        self.stop_button = ctk.CTkButton(self, text="Остановить", 
                       command=self.app_instance.stop_button_callbck, 
                       fg_color="Red",
                       hover_color="DarkRed",
                       font=ctk.CTkFont(size=16))
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)

class LogsFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.app_inst = app_instance

        self.label = ctk.CTkLabel(self, text="Логи", fg_color="LightSlateGray", text_color="white", corner_radius=6, font=ctk.CTkFont(size=18))
        self.label.grid(row=0, sticky="nsew", pady=10, padx=10)

        self.tk_textbox = ctk.CTkTextbox(self, activate_scrollbars=True, width=550, height=280)
        self.tk_textbox.grid(row=1, sticky="nsew", pady=0, padx=10)
        self.tk_textbox.insert("0.0", "")

        self.user_scrolled_up = False

        self.tk_textbox.bind("<MouseWheel>", self.on_mouse_wheel)
        self.tk_textbox.bind("<KeyPress>", self.on_key_press)

        self.button_frame = ButtonFrame(self, app_instance=self.app_inst)
        self.button_frame.configure(fg_color="#dbdbdb")
        self.button_frame.grid(row=2, column=0)
    
    def log_message(self, message):
        self.tk_textbox.configure(state="normal")
        self.tk_textbox.insert("end", message + "\n")
        self.tk_textbox.configure(state="disabled")

        if not self.user_scrolled_up:
            self.tk_textbox.yview("end")

    def on_mouse_wheel(self, event):
        if event.delta < 0:
            self.user_scrolled_up = False 
        else:
            self.user_scrolled_up = True  

    def on_key_press(self, event):
        if event.keysym in ("Up", "Down", "Prior", "Next"):
            self.user_scrolled_up = True

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        self.geometry("800x400")
        self.title("Парсер шин")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1,weight=1)
        self.resizable(0,1)
        self.checkbox_frame = CheckboxFrame(master=self, title="Выбор сайтов",values=["Дром", "Мосавтошина", "Сайт 3", "Сайт 4"], app_instance=self)
        self.checkbox_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsw")
        self.label_log = LogsFrame(self, app_instance=self)
        self.label_log.grid(row=0, column=1, padx=10, pady=10, sticky="nsw")

        self.log_queue = queue.Queue()
        self.after(100, self.process_log_queue)
        self.is_running = False

    def process_log_queue(self):
        try:
            while True:
                message = self.log_queue.get_nowait()
                self.label_log.log_message(message)
        except queue.Empty:
            pass
        self.after(100, self.process_log_queue)

    def start_button_callbck(self):
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self.run_processing, daemon=True).start()

    def run_processing(self):
        logic.processing(self.log_queue, self)

    def stop_button_callbck(self):
        self.is_running = False
        message = "\nОбработка завершена.\n"
        print(message)

    def apply_button_callbck(self):
        if len(self.checkbox_frame.get())<1:
            print("\nНеобходимо выбрать хотя бы 1 сайт!\n")
            self.toplevel_window = mb.messagebox(title='Ошибка',
                                                  text='Необходимо выбрать\nхотя бы 1 сайт!', 
                                                  button_text='OK', 
                                                  size='200x150',
                                                  center=False)
        else:
            print("\nНастройки применены!\n")
            print("Выбранные сайты:", self.checkbox_frame.get())