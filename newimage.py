import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageFont
import warnings
warnings.filterwarnings("ignore")

# Set a much higher limit to handle huge images (e.g., 1 Gigapixel)
# This prevents the "decompression bomb" error for legitimate large files.
Image.MAX_IMAGE_PIXELS = 1_000_000_000

# ----------- CONFIG -----------
# NOTE: You MUST update this path to where your Real-ESRGAN folder is located.
REAL_ESRGAN_PATH = r"C:\Users\ADMIN\Desktop\Real-ESRGAN"
OUTPUT_DIR = os.path.join(REAL_ESRGAN_PATH, "results")
MODEL_CHOICES = ["RealESRGAN_x4plus", "RealESRGAN_x4plus_anime_6B", "realesr-general-x4v3"] # Added a common general model
SCALE_CHOICES = ["4", "8", "16"] # Available output scale factors
# ------------------------------

class ESRGAN_GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ AI Image Upscaler - Next-Gen Slider Edition")

        # Define modern premium black colors (INSANE THEME)
        self.bg_color = "#0a0a0a"       # Near Black Background
        self.accent_color = "#00ffff"   # Electric Cyan Accent
        self.text_color = "#ffffff"     # Pure White Text
        self.secondary_color = "#1a1a1a" # Dark Gray/Black Container (Slightly lighter than bg)

        self.root.geometry("1000x800")
        self.root.config(bg=self.bg_color)
        self.root.resizable(True, True)

        # UI Vars
        self.input_path = tk.StringVar()
        self.model_choice = tk.StringVar(value=MODEL_CHOICES[0])
        self.scale_factor = tk.StringVar(value=SCALE_CHOICES[0]) # New scale factor variable
        self.upscaling_lock = threading.Lock()
        self.status_label_animation = None

        # Image State for Slider
        self.original_photo = None  # PIL Image object
        self.upscaled_photo = None  # PIL Image object
        self.slider_pos = 0.5       # Slider position (0.0 to 1.0)

        # TK Image holders (must be stored to prevent garbage collection)
        self.original_tk = None
        self.upscaled_tk = None
        self.clipped_upscaled_tk = None

        self.configure_style()
        self.create_ui()

    def configure_style(self):
        style = ttk.Style()
        style.theme_use('default')

        # General Style
        style.configure('.', background=self.bg_color, foreground=self.text_color, font=("Inter", 10))

        # Title Label Style
        style.configure('Title.TLabel', background=self.bg_color, foreground=self.accent_color, font=("Inter", 28, "bold"))

        # Frame Style
        style.configure('Dark.TFrame', background=self.bg_color)

        # Button Style
        style.configure('TButton',
                        background=self.secondary_color,
                        foreground=self.text_color,
                        relief="flat",
                        padding=12, # Slightly larger buttons
                        font=("Inter", 12, "bold"))
        style.map('TButton',
                 background=[('active', self.accent_color)],
                 foreground=[('active', self.bg_color)]) # Button text turns dark when active

        # Accent Button Style
        style.configure('Accent.TButton', background=self.accent_color, foreground=self.bg_color) # Cyan button with Black text
        style.map('Accent.TButton',
                 background=[('active', self.secondary_color)],
                 foreground=[('active', self.accent_color)]) # Button text turns cyan when active

        # Progress Bar Style
        style.configure('TProgressbar', background=self.accent_color, troughcolor=self.secondary_color, thickness=18)

        # Status Label Style
        style.configure('Status.TLabel', background=self.bg_color, foreground=self.text_color, font=("Inter", 11, "italic"))

    def create_ui(self):
        # --- Control Panel (Top) ---
        control_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="25 15 25 15")
        control_frame.pack(side="top", fill="x")

        ttk.Label(control_frame, text="AI Image Upscaler", style='Title.TLabel').pack(pady=(5, 15))

        # Input, Model, and Scale Selection Row
        input_model_scale_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        input_model_scale_frame.pack(pady=10)

        # File Chooser
        ttk.Entry(input_model_scale_frame, textvariable=self.input_path, width=30, font=("Inter", 11)).grid(row=0, column=0, padx=10, ipady=6)
        ttk.Button(input_model_scale_frame, text="📂 Browse Image", command=self.browse_image).grid(row=0, column=1, padx=10)

        # Model Selector
        ttk.Label(input_model_scale_frame, text="Model:", background=self.bg_color, foreground=self.text_color, font=("Inter", 11, "bold")).grid(row=0, column=2, padx=(20, 5))
        model_menu = ttk.OptionMenu(input_model_scale_frame, self.model_choice, self.model_choice.get(), *MODEL_CHOICES)
        model_menu.grid(row=0, column=3, padx=10)

        # Scale Factor Selector (NEW)
        ttk.Label(input_model_scale_frame, text="Scale:", background=self.bg_color, foreground=self.text_color, font=("Inter", 11, "bold")).grid(row=0, column=4, padx=(20, 5))
        scale_menu = ttk.OptionMenu(input_model_scale_frame, self.scale_factor, self.scale_factor.get(), *SCALE_CHOICES)
        scale_menu.grid(row=0, column=5, padx=10)


        # Action Buttons
        action_status_frame = ttk.Frame(control_frame, style='Dark.TFrame')
        action_status_frame.pack(pady=20, fill="x")
        action_status_frame.grid_columnconfigure(0, weight=1)
        action_status_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(action_status_frame, text="🚀 UPSCALEEE!", style='Accent.TButton', command=self.run_upscale).grid(row=0, column=0, padx=10, sticky="e")
        ttk.Button(action_status_frame, text="📁 Open Output Dir", command=self.open_output).grid(row=0, column=1, padx=10, sticky="w")

        # Progress Bar and Status
        self.progress = ttk.Progressbar(control_frame, orient="horizontal", length=450, mode="indeterminate", style='TProgressbar')
        self.progress.pack(pady=(15, 8))

        self.status_label = ttk.Label(control_frame, text="Status: Ready.", style='Status.TLabel')
        self.status_label.pack(pady=(8, 10))


        # --- Image Panel (Bottom) with Slider ---
        image_frame = ttk.Frame(self.root, style='Dark.TFrame', padding="20 10 20 20")
        image_frame.pack(side="bottom", fill="both", expand=True)
        image_frame.grid_columnconfigure(0, weight=1)
        image_frame.grid_rowconfigure(1, weight=1)

        # Canvas Title
        ttk.Label(image_frame, text="⚡ Before & After Comparison Slider ⚡", background=self.bg_color, foreground=self.accent_color, font=("Inter", 16, "bold")).grid(row=0, column=0, pady=(0, 10), sticky="n")

        # Combined Canvas for Slider
        self.image_canvas = tk.Canvas(image_frame, bg=self.secondary_color, highlightthickness=0)
        self.image_canvas.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)

        # Bind events for resizing and mouse movement
        self.image_canvas.bind('<Configure>', self.on_canvas_resize)
        self.image_canvas.bind('<B1-Motion>', self.on_slider_move)
        self.image_canvas.bind('<ButtonPress-1>', self.on_slider_move) # Allows click to jump

        self.draw_slider() # Initial call to set placeholder

    def get_resized_images(self, img_pil, w, h):
        """Resizes the PIL image to fit the canvas while maintaining aspect ratio."""
        if not img_pil:
            return None, 0, 0

        img_w, img_h = img_pil.size

        # Calculate aspect ratio
        ratio = min(w / img_w, h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)

        # Resize image using LANCZOS for quality
        img_resized = img_pil.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return img_resized, new_w, new_h

    def draw_placeholder(self, w, h, text):
        """Draws a placeholder text on the empty canvas."""
        self.image_canvas.create_text(
            w // 2, h // 2,
            text=text,
            fill=self.text_color,
            font=("Inter", 24, "bold"),
            justify=tk.CENTER
        )
        self.image_canvas.create_text(
            w // 2, h // 2 + 40,
            text="Use 'Browse Image' to start the magic!",
            fill=self.accent_color,
            font=("Inter", 14),
            justify=tk.CENTER
        )

    def draw_slider(self):
        """Draws both images, clips the 'After' image, and draws the interactive slider handle."""
        w = self.image_canvas.winfo_width()
        h = self.image_canvas.winfo_height()
        self.image_canvas.delete("all")

        if not self.original_photo:
            self.draw_placeholder(w, h, "Select an image and upscale to begin.")
            return

        if not self.upscaled_photo:
            # Show 'Before' only if 'After' hasn't been generated yet
            resized_img, img_w, img_h = self.get_resized_images(self.original_photo, w, h)
            x_offset = (w - img_w) // 2
            y_offset = (h - img_h) // 2
            self.original_tk = ImageTk.PhotoImage(resized_img)
            self.image_canvas.create_image(x_offset, y_offset, anchor="nw", image=self.original_tk)
            self.image_canvas.create_text(w // 2, h - 30, text="Awaiting Upscale Result...", fill=self.accent_color, font=("Inter", 14, "bold"))
            return

        # --- 1. Calculate Positioning ---
        # Assuming both images have the same aspect ratio (Real-ESRGAN maintains aspect ratio)
        original_img, img_w, img_h = self.get_resized_images(self.original_photo, w, h)
        upscaled_img, _, _ = self.get_resized_images(self.upscaled_photo, w, h)

        x_offset = (w - img_w) // 2
        y_offset = (h - img_h) // 2

        # --- 2. Draw 'Before' (Original - Full Background) ---
        self.original_tk = ImageTk.PhotoImage(original_img)
        self.image_canvas.create_image(x_offset, y_offset, anchor="nw", image=self.original_tk)

        # --- 3. Draw 'After' (Upscaled - Clipped Foreground) ---
        clip_width = int(img_w * self.slider_pos)

        # Create a clipped copy of the resized upscaled image
        clip_box = (0, 0, clip_width, img_h)
        clipped_upscaled_pil = upscaled_img.crop(clip_box)

        # Create a full-size transparent image and paste the clip onto it
        temp_img = Image.new('RGBA', (img_w, img_h))
        temp_img.paste(clipped_upscaled_pil, (0, 0))

        self.clipped_upscaled_tk = ImageTk.PhotoImage(temp_img)

        # Draw the clipped upscaled image at the same position
        self.image_canvas.create_image(x_offset, y_offset, anchor="nw", image=self.clipped_upscaled_tk)


        # --- 4. Draw Interactive Divider Line and Handle ---
        divider_x = x_offset + clip_width

        # Divider Line (Thicker and more visible)
        self.image_canvas.create_line(divider_x, y_offset, divider_x, y_offset + img_h, fill=self.accent_color, width=4, tags="slider")

        # Draw a custom handle centered vertically
        handle_size = 20
        self.image_canvas.create_oval(
            divider_x - handle_size//2, h//2 - handle_size//2,
            divider_x + handle_size//2, h//2 + handle_size//2,
            fill=self.accent_color, outline=self.bg_color, width=4, tags="slider_handle"
        )
        # Add visual icon on the handle
        self.image_canvas.create_text(
            divider_x, h//2, text="↔", fill=self.bg_color, font=("Inter", 12, "bold"), tags="slider_handle_text"
        )

        # Add labels for Before/After clarity
        self.image_canvas.create_text(x_offset + 30, y_offset + 20, text="BEFORE", fill="white", font=("Inter", 14, "bold"))
        self.image_canvas.create_text(x_offset + img_w - 40, y_offset + 20, text="AFTER", fill="white", font=("Inter", 14, "bold"))


    def on_canvas_resize(self, event):
        """Redraws the slider when the window/canvas size changes."""
        self.draw_slider()

    def on_slider_move(self, event):
        """Handles mouse drag events to update the slider position."""
        if not self.original_photo or not self.upscaled_photo:
             return

        w = self.image_canvas.winfo_width()
        h = self.image_canvas.winfo_height()

        # Get image dimensions to set boundaries
        _, img_w, _ = self.get_resized_images(self.original_photo, w, h)
        x_offset = (w - img_w) // 2

        # Constrain the mouse X position to the image area
        mouse_x = max(x_offset, min(event.x, x_offset + img_w))

        # Calculate new slider position as a percentage (0.0 to 1.0)
        new_pos = (mouse_x - x_offset) / img_w
        self.slider_pos = max(0.01, min(0.99, new_pos)) # Keep it slightly away from the edges

        self.draw_slider() # Redraw the slider instantly

    def flash_label_success(self, canvas):
        """Temporarily flashes the canvas background green upon success."""
        original_bg = canvas.cget("bg")
        # Use a bright electric green to contrast against the black theme
        flash_color = "#39ff14"

        def reset_bg():
            canvas.config(bg=original_bg)

        canvas.config(bg=flash_color)
        self.root.after(300, reset_bg) # Flash for 300ms

    def animate_status(self):
        """Creates a subtle pulsing animation on the status label during processing."""
        if self.upscaling_lock.locked():
            current_color = self.status_label.cget("foreground")

            # Pulse logic: switch between accent (processing) and text color
            if current_color == self.text_color:
                 new_color = self.accent_color
                 new_text = "Status: PROCESSING IMAGE..."
            else:
                 new_color = self.text_color
                 new_text = "Status: Executing Real-ESRGAN..."

            self.status_label.config(text=new_text, foreground=new_color)

            # Schedule the next pulse
            self.status_label_animation = self.root.after(700, self.animate_status)

    def browse_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.webp")])
        if path:
            self.input_path.set(path)
            self.show_image_preview(path, is_result=False)
            self.status_label.config(text="Status: Image selected. Ready to run.")

    def show_image_preview(self, path, is_result=False):
        """Loads the image into the PIL object state and triggers redrawing."""
        try:
            pil_img = Image.open(path).convert("RGB")

            if is_result:
                self.upscaled_photo = pil_img
                self.flash_label_success(self.image_canvas) # Flash the canvas
            else: # Input image
                self.original_photo = pil_img
                # Clear result when loading new input
                self.upscaled_photo = None
                self.slider_pos = 0.5 # Reset slider position

            self.draw_slider() # Redraw the canvas with the new image(s)

        except Exception as e:
            # We are catching all exceptions here, including the MAX_IMAGE_PIXELS error.
            messagebox.showerror("Image Error", f"Could not load image: {e}")
            self.original_photo = None
            self.upscaled_photo = None
            self.draw_slider()

    def run_upscale(self):
        if not self.input_path.get() or not os.path.exists(self.input_path.get()):
            messagebox.showerror("Error", "Please select a valid input image first.")
            return

        if self.upscaling_lock.locked():
            messagebox.showwarning("Busy", "An upscaling process is already running. Please wait.")
            return

        def process():
            self.upscaling_lock.acquire()
            self.root.after(0, self.animate_status) # Start pulsing animation
            self.root.after(0, lambda: self.progress.start(10)) # Start indeterminate animation

            try:
                os.makedirs(OUTPUT_DIR, exist_ok=True)

                # Construct the command, including the new scale factor
                cmd = [
                    "python", os.path.join(REAL_ESRGAN_PATH, "inference_realesrgan.py"),
                    "-n", self.model_choice.get(),
                    "-i", self.input_path.get(),
                    "-o", OUTPUT_DIR,
                    "--fp32",
                    "-s", self.scale_factor.get() # Pass the desired output scale (4, 8, or 16)
                ]

                self.root.after(0, lambda: self.status_label.config(text="Status: Executing Real-ESRGAN..."))

                result = subprocess.run(cmd, cwd=REAL_ESRGAN_PATH, capture_output=True, text=True, check=True)

                # Real-ESRGAN suffixes the filename
                base_name, ext = os.path.splitext(os.path.basename(self.input_path.get()))
                out_name = f"{base_name}_out{ext}"
                result_path = os.path.join(OUTPUT_DIR, out_name)

                if os.path.exists(result_path):
                    # Load the result into the state and draw the slider
                    self.root.after(0, lambda: self.show_image_preview(result_path, is_result=True))
                    self.root.after(0, lambda: messagebox.showinfo("Success!", f"Upscale complete! Saved to:\n{result_path}"))
                else:
                    self.root.after(0, lambda: messagebox.showerror("Failure", "Upscale script ran, but output file not found. Check console for details."))

            except subprocess.CalledProcessError as e:
                error_message = f"Subprocess Error:\n{e.stderr}\nCheck your REAL_ESRGAN_PATH and dependencies."
                self.root.after(0, lambda: messagebox.showerror("Upscale Failed (Subprocess)", error_message))
            except FileNotFoundError:
                error_message = "Python or inference script not found. Check if Real-ESRGAN is correctly installed and REAL_ESRGAN_PATH is correct."
                self.root.after(0, lambda: messagebox.showerror("Upscale Failed (Path)", error_message))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Upscale Failed", f"An unexpected error occurred: {str(e)}"))
            finally:
                if self.status_label_animation:
                    self.root.after_cancel(self.status_label_animation)
                self.root.after(0, lambda: self.progress.stop())
                self.root.after(0, lambda: self.status_label.config(text="Status: Done!", foreground=self.text_color))
                self.upscaling_lock.release()

        # Start the processing in a separate thread
        threading.Thread(target=process).start()

    def open_output(self):
        """Opens the output directory in the file explorer."""
        try:
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR, exist_ok=True)
                messagebox.showinfo("Info", "Output directory created.")
            os.startfile(OUTPUT_DIR)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open directory: {e}")

if __name__ == "__main__":
    # Ensure dependencies are available for Image Preview
    try:
        Image.new('RGB', (1, 1))
    except ImportError:
        messagebox.showerror("Dependency Error", "Pillow (PIL) library is required. Please install it using: pip install Pillow")
        exit()

    root = tk.Tk()
    app = ESRGAN_GUI(root)
    root.mainloop()
