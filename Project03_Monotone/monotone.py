import tkinter as tk
from tkinter import messagebox

window = tk.Tk()
window.title("تشخیص یکنوایی")

window.configure(bg='dark gray')

canvas = tk.Canvas(window, width=250, height=400, bg='powder blue')
canvas.pack(pady=20)  

points = []
polyline = None

# Functions
def AddPoint(event):
    x, y = event.x, event.y
    points.append((x, y))
    DrawPoint(x, y)
    DrawPolyline()

def DrawPoint(x, y):
    radius = 5
    canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill='red')

def DrawPolyline():
    global polyline
    if len(points) > 1:
        coords = []
        for point in points:
            for coord in point:
                coords.append(coord)
        polyline = canvas.create_line(coords, fill='yellow', width=3)

def CheckMonotone():
    if len(points) < 2:
        messagebox.showinfo("!خطا", "!لطفا حداقل دو نقطه ترسیم نمائید")
        return
    increasing = True
    decreasing = True
    for i in range(1, len(points)):
        if points[i][1] > points[i - 1][1]:
            decreasing = False
        elif points[i][1] < points[i - 1][1]:
            increasing = False
    if increasing:
        messagebox.showinfo("نتیجه", "پلی لاین یکنوا است")
    elif decreasing:
        messagebox.showinfo("نتیجه", "پلی لاین یکنوا است")
    else:
        messagebox.showinfo("نتیجه", "پلی لاین یکنوا نیست")

def ClearPoints():
    global polyline
    points.clear()
    canvas.delete("all")
    polyline = None

check_button = tk.Button(window, text="چک کردن یکنوایی", command=CheckMonotone, bg='lightgreen', font=('Arial', 14), padx=10, pady=5)
check_button.pack(pady=10)

clear_button = tk.Button(window, text="پاک کردن نقاط", command=ClearPoints, bg='salmon', font=('Arial', 14), padx=10, pady=5)
clear_button.pack(pady=10)

canvas.bind("<Button-1>", AddPoint)

window.mainloop()