import os
import subprocess
import sys

# Ensure required libraries are installed
try:
    import qrcode
    from PIL import Image, ImageDraw
except ImportError:
    print("Required packages (qrcode, pillow) not found. Installing them now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "qrcode", "pillow"])
    import qrcode
    from PIL import Image, ImageDraw

def generate_qr_with_logo(name, url, logo_path, fill_color="#1A1A1A", back_color="#FFFFFF", output_dir="qrcodes"):
    # Create the output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print(f"\nGenerating QR code for {name} ({fill_color} on {back_color})...")
    
    # Configure QR code parameters with High Error Correction
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    qr.add_data(url)
    qr.make(fit=True)
    
    # Generate the base QR image as RGB with the requested colors
    qr_img = qr.make_image(fill_color=fill_color, back_color=back_color).convert("RGB")
    qr_width, qr_height = qr_img.size
    
    if os.path.exists(logo_path):
        try:
            # Open logo and convert to RGBA
            logo = Image.open(logo_path).convert("RGBA")
            
            # Calculate dimensions (logo should occupy ~20% of QR code size)
            logo_max_size = int(qr_width * 0.20)
            
            # Scale logo to be a square of logo_max_size
            logo = logo.resize((logo_max_size, logo_max_size), Image.Resampling.LANCZOS)
            
            # Create a circular mask for the logo
            mask = Image.new("L", (logo_max_size, logo_max_size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, logo_max_size, logo_max_size), fill=255)
            
            # Apply circular mask to the logo
            logo_circle = Image.new("RGBA", (logo_max_size, logo_max_size), (0, 0, 0, 0))
            logo_circle.paste(logo, (0, 0), mask=mask)
            
            # Create a white circular container slightly larger than the logo
            # Using white ensures the logo stands out nicely regardless of the QR background color
            padding = 6
            container_size = logo_max_size + padding * 2
            container = Image.new("RGBA", (container_size, container_size), (0, 0, 0, 0))
            container_draw = ImageDraw.Draw(container)
            container_draw.ellipse((0, 0, container_size, container_size), fill=(255, 255, 255, 255))
            
            # Paste the circular logo in the center of the white circular container
            container.paste(logo_circle, (padding, padding), mask=logo_circle)
            
            # Paste the final container into the center of the QR image
            pos = ((qr_width - container_size) // 2, (qr_height - container_size) // 2)
            qr_img.paste(container, pos, mask=container)
            print(f"Successfully embedded logo into QR code.")
            
        except Exception as e:
            print(f"Error embedding logo: {e}. Generating standard QR instead.")
    else:
        print(f"Warning: Logo file not found at '{logo_path}'. Generating standard QR code.")

    # Save the file
    filename = f"{name.lower().replace(' ', '_')}_qr.png"
    filepath = os.path.join(output_dir, filename)
    qr_img.save(filepath)
    print(f"Saved: {filepath}")
    return filepath

if __name__ == "__main__":
    # Define the links and their styling configuration
    # Note: Modern QR readers handle light-on-dark (inverted) QR codes perfectly.
    # To keep the colors vibrant, we set the brand color as background (back_color)
    # and white as the QR pattern (fill_color).
    configs = [
        {
            "name": "Portfolio",
            "url": "https://tusharahul.netlify.app/",
            "fill_color": "#FFFFFF",
            "back_color": "#FF7A00"  # Vibrant Orange
        },
        {
            "name": "Linkedin",
            "url": "https://www.linkedin.com/in/tusha-rahul/",
            "fill_color": "#FFFFFF",
            "back_color": "#0A66C2"  # Official LinkedIn Blue
        },
        {
            "name": "Github",
            "url": "https://github.com/Rahul6158/",
            "fill_color": "#FFFFFF",
            "back_color": "#181717"  # Official GitHub Dark Grey/Black
        }
    ]
    
    # Path to the logo image
    logo_file = r"D:\Downloads\img.jpeg"
    
    print("Starting Customized QR Code generation...")
    generated_files = []
    for config in configs:
        path = generate_qr_with_logo(
            name=config["name"],
            url=config["url"],
            logo_path=logo_file,
            fill_color=config["fill_color"],
            back_color=config["back_color"]
        )
        generated_files.append(path)
        
    print("\nAll QR codes generated successfully with custom branding colors!")
    for file in generated_files:
        print(f"- {os.path.abspath(file)}")
