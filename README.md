# QR Studio 🎨

A visually stunning, feature-rich Flask web application to design and export customized, scan-safe branded QR codes. Easily configure custom colors, gradients, upload logos with custom shapes and drop shadows, adjust module and eye styles, and preview changes instantly without page refreshes.

---

## ✨ Features

- **🚀 Live Dynamic Preview**: High-speed, non-blocking AJAX updates as you change inputs, select styles, or modify colors.
- **⚡ Brand Presets**: Quick-select buttons to configure optimized themes for LinkedIn, GitHub, and Portfolios.
- **🌈 Advanced Colors & Gradients**: Choose high-contrast solid colors or configure linear/radial gradients using responsive color pickers.
- **🖼️ Smart Logo Embedding**:
  - Custom shapes (Circle, Rounded Square, Square).
  - Scale adjustment slider (10% to 30% of QR code width).
  - Optional white border backing to prevent QR module clashes.
  - Custom-generated Gaussian drop shadow layer.
- **📐 Premium QR Styling**:
  - Customizable modules (Classic Square, Rounded Modules, Circles/Dots, Gapped Square, and Diamonds).
  - Customized eye shapes (Classic, Rounded, Circle, and Modern Border).
  - Margin border size adjustment slider.
- **💾 Easy Export**: Instant download as PNG or one-click copy to clipboard.
- **🖥️ Premium Responsive UI**: Dark theme featuring floating animated background blobs, glassmorphic cards, and micro-interactions.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.12, Flask, Pillow (PIL), `qrcode`
- **Frontend**: HTML5, Vanilla CSS (Glassmorphism design, keyframe animations), JavaScript (Fetch API, FileReader API, Clipboard API)
- **Icons**: FontAwesome v6

---

## 🚀 Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/qr-studio.git
cd qr-studio
```

### 2. Install dependencies

Ensure Python is installed, then run:

```bash
pip install -r requirements.txt
```

### 3. Run the application

```bash
python app.py
```

Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 📁 Project Structure

```
qr-studio/
├── app.py                  # Flask Application server & routing API
├── generator/
│   └── qr_generator.py     # Custom module/eye drawers & logo processors
├── static/
│   ├── css/
│   │   └── style.css       # Premium CSS stylesheet with glassmorphism
│   └── js/
│       └── script.js       # Live preview and file drop handlers
├── templates/
│   └── index.html          # Main application page template
├── requirements.txt        # Project library requirements
└── README.md               # Repository documentation
```
