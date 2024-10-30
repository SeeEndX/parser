import signal
import parser_logic.checkpoint as ch
from gui import views as vi
from functools import partial

def main():
    app = vi.App()
    signal.signal(signal.SIGINT, partial(ch.signal_handler, app_instance=app))
    app.mainloop()

if __name__ == "__main__":
    main()