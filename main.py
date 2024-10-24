import signal
import parser_logic.checkpoint as ch
import gui.views as v

def main():
    signal.signal(signal.SIGINT, ch.signal_handler) 
    v.init_window()

if __name__ == "__main__":
    main()