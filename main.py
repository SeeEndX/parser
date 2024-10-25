import signal
import parser_logic.checkpoint as ch
from gui import views as vi

def main():
    app = vi.App()
    app.mainloop()
    signal.signal(signal.SIGINT, ch.signal_handler) 

if __name__ == "__main__":
    main()