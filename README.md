# Image-Upscaler
🧠 AI Image Upscaler (Offline)
Enhance your images up to 16× resolution with AI — all without needing an internet connection!
🚀 Overview

This project is an offline AI-powered image upscaler built using Real-ESRGAN, capable of improving image quality and resolution up to 16×.
It can recover lost textures, details, and colors — making low-resolution images look ultra-sharp and realistic.

💡 Features

🧩 Offline Support — works fully offline (no API or cloud needed).

🎨 16× Image Upscaling — crystal-clear zoom with fine detail restoration.

⚡ Fast Processing — optimized for performance using pre-trained ESRGAN models.

🖼️ Batch Mode — upscale multiple images at once.

🪶 Lightweight & Simple UI (optional if you added a GUI)

🛠️ Tech Stack

Python 3.10+

Real-ESRGAN (PyTorch)

OpenCV

NumPy

Tkinter / Gradio (optional)

📂 Installation
git clone https://github.com/yourusername/AI-Image-Upscaler.git
cd AI-Image-Upscaler
pip install -r requirements.txt


Download the Real-ESRGAN model weights:
Official Model Repo

🧑‍💻 Usage
python upscale.py -i input_folder -o output_folder --scale 16


Example:

python upscale.py -i images -o results --scale 4
🏆 Highlights

Runs completely offline

Preserves texture and color accuracy

Optimized for real-world photos

💬 Author

Hrushikesh G. (R.G)
🎓 B.Tech CSE Student | Passionate about AI & Computer Vision
📫 Connect on LinkedIn
📄 License

