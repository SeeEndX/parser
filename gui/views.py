import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox as mb
from parser_logic import logic
import queue
import threading
import tkinter as tk

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
        #self.configure(fg_color="transparent")
        self.values = values
        self.title = title

        self.checkboxes = []
        self.app_instance = app_instance

        self.title = ctk.CTkLabel(self, text=self.title, fg_color="#2cc985", text_color="Black", corner_radius=6, font=ctk.CTkFont(size=16))
        self.title.grid(row=0, column=0, padx=10, pady=(10,5), sticky="ew")

        for i, value in enumerate(self.values):
            checkbox = ctk.CTkCheckBox(self, text=value, font=ctk.CTkFont(size=12))
            checkbox.grid(row=i+1, column=0, padx=10, pady=(10, 10), sticky="ew")
            self.checkboxes.append(checkbox)

        if "Дром" in self.values:
            self.checkboxes[self.values.index("Дром")].select()

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
        self.configure(fg_color="transparent")

        self.app_instance = app_instance
        
        photo_image = tk.PhotoImage(file="gui/resources/play.png")
        photo_image = photo_image.subsample(12)

        self.start_button = ctk.CTkButton(self, 
                                          text="",
                                          image=photo_image,
                                          command=self.app_instance.start_button_callbck,
                                          font=ctk.CTkFont(size=14),
                                          width=100,
                                          height=25,
                                          border_width=2)
        self.start_button.grid(row=0, column=0, padx=10, pady=10)
        self.stop_button = ctk.CTkButton(self, 
                                         text="Остановить", 
                                         command=self.app_instance.stop_button_callbck, 
                                         fg_color="Red",
                                         hover_color="DarkRed",
                                         font=ctk.CTkFont(size=14),
                                         width=100,
                                         height=25,
                                         border_width=2)
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)

class LogsFrame(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.app_inst = app_instance
        #self.configure(fg_color="transparent") 

        self.label = ctk.CTkLabel(self, text="Логи", fg_color="#2cc985", text_color="Black", corner_radius=6, font=ctk.CTkFont(size=16))
        self.label.grid(row=0, sticky="nsew", pady=10, padx=10)

        self.tk_textbox = ctk.CTkTextbox(self, activate_scrollbars=True, width=560, height=280, border_color="#2cc985", border_width=2, font=ctk.CTkFont(size=12))
        self.tk_textbox.grid(row=1, sticky="nsew", pady=2, padx=10)
        self.tk_textbox.insert("0.0", "")

        self.user_scrolled_up = False

        self.tk_textbox.bind("<MouseWheel>", self.on_mouse_wheel)
        self.tk_textbox.bind("<KeyPress>", self.on_key_press)

        self.button_frame = ButtonFrame(self, app_instance=self.app_inst)
        self.button_frame.grid(row=2, column=0, sticky="w", padx=10)
    
    def log_message(self, message, color, weight):
        self.tk_textbox.configure(state="normal")

        tag_name = f"{color}_{weight}"
        if tag_name not in self.tk_textbox.tag_names():
            self.tk_textbox.tag_config(tag_name, foreground=color)

        self.tk_textbox.insert("end", message + "\n", tag_name)
    
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
        self.checkbox_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.label_log = LogsFrame(self, app_instance=self)
        self.label_log.grid(row=0, column=1, padx=10, pady=10, sticky="nesw")

        self.log_queue = queue.Queue()
        self.after(100, self.process_log_queue)
        self.is_running = threading.Event()

    def process_log_queue(self):
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                print("Received log entry:", log_entry)
                if isinstance(log_entry, tuple):
                    message, color, weight = log_entry
                    self.label_log.log_message(message, color, weight)
                else:
                    self.label_log.log_message(log_entry, "black", "normal")
        except queue.Empty:
            pass
        self.after(100, self.process_log_queue)

    def start_button_callbck(self):
        selected_sites = self.checkbox_frame.get()
        if not selected_sites:
            mb.messagebox(title='Ошибка',
                          text='Необходимо выбрать\nхотя бы 1 сайт!', 
                          button_text='OK', 
                          size='200x150',
                          center=False)
            return
        if not self.is_running.is_set():
            self.is_running.set()
            threading.Thread(target=self.run_processing, args=(selected_sites,), daemon=True).start()

    def run_processing(self, selected_sites):
        logic.processing(self.log_queue, self, selected_sites)

    def stop_button_callbck(self):
        self.is_running.clear()

    def apply_button_callbck(self):
        if len(self.checkbox_frame.get())<1:
            self.toplevel_window = mb.messagebox(title='Ошибка',
                                                  text='Необходимо выбрать\nхотя бы 1 сайт!', 
                                                  button_text='OK', 
                                                  size='200x150',
                                                  center=False)
        else:

            message = f"\nНастройки применены!\nВыбранные сайты:{self.checkbox_frame.get()}"
            print(message)
            self.log_queue.put((message, "LimeGreen", 'normal'))