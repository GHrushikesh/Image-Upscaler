import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

# --- Paths ---
MODEL_NAME = "realesrgan-ncnn-vulkan.exe"
OUTPUT_NAME = "output.png"

class DSLRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DSLR 8K AI Upscaler")
        self.root.geometry("900x600")
        self.root.iconbitmap(default='')  # Optional icon
        self.style = ttk.Style("cosmo")
        self.root.configure(bg="#0e0e0e")

        self.image_path = None
        self.original_img = None
        self.upscaled_img = None

        # --- Title ---
        title = ttk.Label(root, text="📸 DSLR 8K AI UPSCALER", font=("Segoe UI", 20, "bold"), foreground="#00ffcc")
        title.pack(pady=15)

        # --- Image Frame ---
        self.canvas = tk.Canvas(root, width=800, height=400, bg="#1e1e1e", highlightthickness=0)
        self.canvas.pack()

        # --- Buttons ---
        btn_frame = ttk.Frame(root)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Upload Photo", command=self.upload_image, bootstyle="info-outline").grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Enhance to DSLR", command=self.upscale_image, bootstyle="success-outline").grid(row=0, column=1, padx=10)
        ttk.Button(btn_frame, text="Compare Before/After", command=self.animate_compare, bootstyle="warning-outline").grid(row=0, column=2, padx=10)

    def upload_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png")])
        if path:
            self.image_path = path
            self.show_image(path)

    def show_image(self, path):
        img = Image.open(path).resize((800, 400))
        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.create_image(400, 200, image=self.tk_img)

    def upscale_image(self):
        if not self.image_path:
            messagebox.showwarning("No Image", "Please upload an image first.")
            return

        command = [
            MODEL_NAME,
            "-i", self.image_path,
            "-o", OUTPUT_NAME,
            "-n", "realesrgan-x4plus",
            "-s", "4"
        ]
        subprocess.run(command)
        messagebox.showinfo("Done", "Your image has been enhanced to DSLR 8K quality!")
        self.upscaled_img = OUTPUT_NAME
        self.show_image(OUTPUT_NAME)

    def animate_compare(self):
        if not self.upscaled_img:
            messagebox.showwarning("No Upscaled Image", "Enhance image first!")
            return

        orig = Image.open(self.image_path).resize((900, 1600))
        upsc = Image.open(self.upscaled_img).resize((900, 1600))

        for alpha in range(0, 101, 5):
            blended = Image.blend(orig, upsc, alpha / 100.0)
            tk_blend = ImageTk.PhotoImage(blended)
            self.canvas.create_image(400, 200, image=tk_blend)
            self.root.update_idletasks()
            self.root.after(30)
        messagebox.showinfo("Comparison", "Animated Before/After Completed!")

# --- Run App ---
if __name__ == "__main__":
    root = ttk.Window(themename="cyborg")
    app = DSLRApp(root)
    root.mainloop()
