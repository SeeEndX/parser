import customtkinter as ctk
from CustomTkinterMessagebox import CTkMessagebox as mb
from parser_logic import logic

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

    def start_button_callbck(self):
            logic.processing()
            print("Обработка началась...\n\n")

    def stop_button_callbck(self):
        print("\nОбработка завершена.\n")

class ToplevelWindow(ctk.CTkToplevel):
    def __init__(self, master, text):
        super().__init__(master)
        self.geometry("200x150")
        self.label = ctk.CTkLabel(self, text=text)
        self.label.pack(padx=20, pady=20)  

app = None

def init_window():
    app = App()
    app.checkbox_frame = CheckboxFrame(app, title="Выбор сайтов",values=["Дром", "Мосавтошина", "Сайт 3", "Сайт 4"])
    app.checkbox_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsw")
    app.label_log = LogsFrame(app)
    app.label_log.grid(row=0, column=1, padx=10, pady=10, sticky="nsw")
    app.mainloop()

class CheckboxFrame(ctk.CTkFrame):
    def __init__(self, master, title, values):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.values = values
        self.title = title

        self.checkboxes = []

        self.title = ctk.CTkLabel(self, text=self.title, fg_color="LightSlateGray", text_color="white", corner_radius=6, font=ctk.CTkFont(size=18))
        self.title.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="ew")

        for i, value in enumerate(self.values):
            checkbox = ctk.CTkCheckBox(self, text=value, font=ctk.CTkFont(size=14))
            checkbox.grid(row=i+1, column=0, padx=10, pady=(10, 0), sticky="w")
            self.checkboxes.append(checkbox)
        
        self.apply_button = ctk.CTkButton(self, text="Применить настройки", command=self.apply_button_callbck, font=ctk.CTkFont(size=14), text_color="Black", fg_color="White", hover_color="DarkGray",)
        self.apply_button.grid(row=5, column=0, padx=10, pady=(155,0))

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

    def get(self):
        checked_checkboxes = []
        for checkbox in self.checkboxes:
            if checkbox.get() == 1:
                checked_checkboxes.append(checkbox.cget("text"))
        return checked_checkboxes
    
class ButtonFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.start_button = ctk.CTkButton(self, text="Начать", command=app.start_button_callbck(app),font=ctk.CTkFont(size=16))
        self.start_button.grid(row=0, column=0, padx=10, pady=10)
        self.stop_button = ctk.CTkButton(self, text="Остановить", 
                       command=app.stop_button_callbck(app), 
                       fg_color="Red",
                       hover_color="DarkRed",
                       font=ctk.CTkFont(size=16))
        self.stop_button.grid(row=0, column=1, padx=10, pady=10)

        

class LogsFrame(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.grid_columnconfigure(0, weight=1)

        self.label = ctk.CTkLabel(self, text="Логи", fg_color="LightSlateGray", text_color="white", corner_radius=6, font=ctk.CTkFont(size=18))
        self.label.grid(row=0, sticky="nsew", pady=10, padx=10)

        self.tk_textbox = ctk.CTkTextbox(self, activate_scrollbars=True, width=550, height=280)
        self.tk_textbox.grid(row=1, sticky="nsew", pady=0, padx=10)
        self.tk_textbox.insert("0.0", "new text to insert")
        self.tk_textbox.configure(state="disabled")

        self.button_frame = ButtonFrame(self)
        self.button_frame.configure(fg_color="#dbdbdb")
        self.button_frame.grid(row=2, column=0)#, sticky="nswe")