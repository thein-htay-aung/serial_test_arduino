import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import time
from configparser import ConfigParser
import threading
from queue import Queue

import serial


class Form(tk.Frame):
    
    def __init__(self, container):
        tk.Frame.__init__(self, container)

        self.config(bg="#87CEEB")

        self.font1 = ("Helvetica", 10)          
        self.font2 = ("Helvetica", 14)          
        
        self.frm_border_options = {"highlightbackground": "grey", "highlightcolor": "blue", "highlightthickness": 1, "border": 0}

        # +++++++++++++++++++++++++++++++++++++++

        self._exit_read = False
        self._exit_ui = False

        self.queue = Queue()

        self.arduino_con = None

        connection_thread = threading.Thread(target=self.connect)
        connection_thread.start()

        self.start_ui()

        time.sleep(2)
        self.update_ui()


    def start_ui(self):

        self.f1 = tk.Frame(self, bg="white", **self.frm_border_options)
        self.f1.pack(padx=0, pady=20)

        # +++++++++++++++++++++++++++++++++++++++

        self.warning = tk.StringVar()
        self.warning_lb = tk.Label(self.f1, text="", font=self.font2, bg=self.f1["bg"], fg="red")
        self.warning_lb.pack(side="top", padx=20, pady=10)

        # +++++++++++++++++++++++++++++++++++++++

        self.f1_1 = tk.Frame(self.f1, bg=self.f1["bg"])
        self.f1_1.pack(side="top", padx=20, pady=20)

        # ----------------------------------------

        self.lb = tk.Label(self.f1_1, text="A Value : ", font=self.font1, bg=self.f1_1["bg"])
        self.lb.grid(row=1, column=1, padx=0, pady=10, sticky="e")

        self.a_value = tk.StringVar()
        self.a_value_box = ttk.Entry(self.f1_1, font=self.font1, width=20, textvariable=self.a_value, state="readonly", justify="center")
        self.a_value_box.grid(row=1, column=2, padx=0, pady=10, sticky="w")     

        # ----------------------------------------    

        self.lb = tk.Label(self.f1_1, text="B Value : ", font=self.font1, bg=self.f1_1["bg"])
        self.lb.grid(row=2, column=1, padx=0, pady=10, sticky="e")

        self.b_value = tk.StringVar()
        self.b_value_box = ttk.Entry(self.f1_1, font=self.font1, width=20, textvariable=self.b_value, state="readonly", justify="center")
        self.b_value_box.grid(row=2, column=2, padx=0, pady=10, sticky="w") 

        # ----------------------------------------    

        self.lb = tk.Label(self.f1_1, text="C Value : ", font=self.font1, bg=self.f1_1["bg"])
        self.lb.grid(row=3, column=1, padx=0, pady=10, sticky="e")

        self.c_value = tk.StringVar()
        self.c_value_box = ttk.Entry(self.f1_1, font=self.font1, width=20, textvariable=self.c_value, justify="center")
        self.c_value_box.grid(row=3, column=2, padx=0, pady=10, sticky="w") 

        # ----------------------------------------

        self.write_btn = tk.Button(self.f1_1, font=self.font1, text="Calibrate", width=10, bg="green", fg="white", command=self.write)
        self.write_btn.grid(row=4, column=2, padx=0, pady=20, sticky="e")   

    def connect(self):

        arduino_config = self.read_config(section="arduino")
        self.plc_resolution = int(arduino_config["resolution"])

        com = arduino_config["com"]
        baud = arduino_config["baud"]

        try:
            self.arduino_con = serial.Serial(com, baud)

            # ++++++++++++++++++++++++++++++++++++++++++++++++++

            reading_thread = threading.Thread(target=self.read)
            reading_thread.start()

            # self.read()
        except:
            self.warning.set("Connection Failed.")
            self.arduino_con = None
        
    def disconnect(self):

        if self.arduino_con is not None:
            self.arduino_con.close()

    def read(self):

        while not self.master._exit:

            try:                
            
                byte_value = self.arduino_con.readline()
                str_value = byte_value.decode().strip()

                if "," in str_value:

                    values = str_value.split(",")                

                    wk_dict = {
                        "a": values[0].split(":")[1],
                        "b": values[1].split(":")[1],
                        "c": values[2].split(":")[1],
                    }

                self.queue.put(wk_dict)

            except Exception as err:
                print(str(err))

        self._exit_read = True
        self.disconnect()



    def update_ui(self):

        if self.master._exit:
            self._exit_ui = True
            return False
        
        try:
            wk_dict = self.queue.get(block=False)
            self.a_value.set(wk_dict["a"])
            self.b_value.set(wk_dict["b"])
            self.c_value.set(wk_dict["c"])            

        except:
            pass

        print(self.queue.qsize())

        self.warning_lb["text"] = "Reading..."

        self.update()

        # +++++++++++++++++++++++++++++++++++++++

        self.after(400, self.update_ui)


    def write(self):

        a_value = self.a_value.get()
        b_value = self.b_value.get()
        c_value = self.c_value.get()

        msg = f"{a_value}, {b_value}, {c_value}"

        messagebox.showinfo("Info", msg)


    def read_config(self, section: str):

        file_dir = os.path.join(os.path.dirname(__file__), "config.ini") 
        try:
            cfg = ConfigParser()
            cfg.read(file_dir)

            return dict(cfg.items(section))

        except:
            messagebox.showerror("Error", "Can't read setting file.")
            return False

    def write_config(self, section: str, option: str, value: str):
        
        file_dir = os.path.join(os.path.dirname(__file__), "config.ini")
        try:
            cfg = ConfigParser()
            cfg.read(file_dir)
            cfg.set(section, option, str(value))

            with open(file_dir, "w") as config_file:
                cfg.write(config_file)

                return True
        except:
            messagebox.showerror("Error", "Can't update setting file.")
            return False



class App(tk.Tk):

    def __init__(self):
        tk.Tk.__init__(self)

        # ++++++++++++++++++++++++++++++++++++++++++

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        width = 600
        height = 350

        start_x = int((screen_width - width) / 2)
        start_y = int((screen_height - height) / 3)

        # ++++++++++++++++++++++++++++++++++++++++++

        self.config(bg="white")
        self.geometry(f"{width}x{height}")
        self.geometry(f"+{start_x}+{start_y}")

        self.title("Shutter Position Calibrator_v0.0.1")

        # ++++++++++++++++++++++++++++++++++++++++++

        self._exit = False
        self.protocol("WM_DELETE_WINDOW", self.exit_system)

        self.form = Form(self)
        self.form.pack(side="top", anchor="w", fill="both", expand=True) 

        # ++++++++++++++++++++++++++++++++++++++++++


    def exit_system(self):

        self._exit = True

        while True:
            if self.form._exit_read == True and self.form._exit_ui == True:
                break
            self.update()

        self.destroy()



if __name__ == "__main__":
    app = App()
    ico_dir = os.path.join(os.path.dirname(__file__), "favicon.ico") 
    app.iconbitmap(ico_dir)    
    app.mainloop()
        
