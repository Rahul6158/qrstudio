import os
import io
import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import (
    SquareModuleDrawer,
    GappedSquareModuleDrawer,
    CircleModuleDrawer,
    RoundedModuleDrawer,
)
from qrcode.image.styles.colormasks import (
    SolidFillColorMask,
    RadialGradiantColorMask,
    HorizontalGradiantColorMask,
    VerticalGradiantColorMask,
)
from qrcode.image.styles.moduledrawers.base import QRModuleDrawer

# Custom Diamond Module Drawer
class DiamondModuleDrawer(QRModuleDrawer):
    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.imgDraw = ImageDraw.Draw(self.img._img)

    def drawrect(self, box, is_active: bool):
        if is_active:
            (x0, y0), (x1, y1) = box
            cx = (x0 + x1) / 2
            cy = (y0 + y1) / 2
            points = [(cx, y0), (x1, cy), (cx, y1), (x0, cy)]
            self.imgDraw.polygon(points, fill=self.img.paint_color)

def hex_to_rgb(hex_str):
    hex_str = hex_str.lstrip('#')
    if len(hex_str) == 3:
        hex_str = ''.join(c*2 for c in hex_str)
    return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))

def get_module_drawer(style):
    drawers = {
        'classic': SquareModuleDrawer(),
        'gapped_square': GappedSquareModuleDrawer(),
        'circle': CircleModuleDrawer(),
        'rounded': RoundedModuleDrawer(),
        'diamond': DiamondModuleDrawer(),
    }
    return drawers.get(style, SquareModuleDrawer())

def get_eye_drawer(style):
    drawers = {
        'classic': SquareModuleDrawer(),
        'rounded': RoundedModuleDrawer(),
        'circle': CircleModuleDrawer(),
        'modern': GappedSquareModuleDrawer(),
    }
    return drawers.get(style, SquareModuleDrawer())

def get_color_mask(gradient_type, back_rgb, fill_rgb, gradient_rgb):
    if gradient_type == 'linear_horizontal':
        return HorizontalGradiantColorMask(back_color=back_rgb, left_color=fill_rgb, right_color=gradient_rgb)
    elif gradient_type == 'linear_vertical':
        return VerticalGradiantColorMask(back_color=back_rgb, top_color=fill_rgb, bottom_color=gradient_rgb)
    elif gradient_type == 'radial':
        return RadialGradiantColorMask(back_color=back_rgb, center_color=fill_rgb, edge_color=gradient_rgb)
    else:  # solid
        return SolidFillColorMask(back_color=back_rgb, front_color=fill_rgb)

def process_logo(logo_img, size, shape, has_border, has_shadow):
    """
    Processes logo to be a square of size x size with requested shape, border, and drop shadow.
    Uses high-quality supersampling for smooth anti-aliased borders and shapes.
    """
    scale = 4
    
    # Force logo to be a square and convert to RGBA
    logo = logo_img.convert("RGBA")
    logo = ImageOps.fit(logo, (size, size), Image.Resampling.LANCZOS)
    
    # Create mask for the shape (supersampled for anti-aliasing)
    mask_size = size * scale
    mask_large = Image.new("L", (mask_size, mask_size), 0)
    mask_draw_large = ImageDraw.Draw(mask_large)
    
    if shape == 'circle':
        mask_draw_large.ellipse((0, 0, mask_size, mask_size), fill=255)
    elif shape == 'rounded_square':
        radius = int(mask_size * 0.25)
        mask_draw_large.rounded_rectangle((0, 0, mask_size, mask_size), radius=radius, fill=255)
    else:  # square
        mask_draw_large.rectangle((0, 0, mask_size, mask_size), fill=255)
        
    mask = mask_large.resize((size, size), Image.Resampling.LANCZOS)
        
    # Crop logo using mask
    logo_cropped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    logo_cropped.paste(logo, (0, 0), mask=mask)
    
    # Calculate container size (includes padding/border)
    padding = 6 if has_border else 0
    container_size = size + padding * 2
    
    # Create container image (transparent) with anti-aliased white border if requested
    if has_border:
        container_size_scaled = container_size * scale
        container_large = Image.new("RGBA", (container_size_scaled, container_size_scaled), (0, 0, 0, 0))
        container_draw_large = ImageDraw.Draw(container_large)
        
        if shape == 'circle':
            container_draw_large.ellipse((0, 0, container_size_scaled, container_size_scaled), fill=(255, 255, 255, 255))
        elif shape == 'rounded_square':
            radius = int(container_size_scaled * 0.25)
            container_draw_large.rounded_rectangle((0, 0, container_size_scaled, container_size_scaled), radius=radius, fill=(255, 255, 255, 255))
        else:  # square
            container_draw_large.rectangle((0, 0, container_size_scaled, container_size_scaled), fill=(255, 255, 255, 255))
            
        container = container_large.resize((container_size, container_size), Image.Resampling.LANCZOS)
    else:
        container = Image.new("RGBA", (container_size, container_size), (0, 0, 0, 0))
        
    # Paste logo in center of container
    container.paste(logo_cropped, (padding, padding), mask=logo_cropped)
    
    # Apply drop shadow if requested
    if has_shadow:
        shadow_offset = 4
        shadow_blur = 6
        shadow_size = container_size + shadow_blur * 2
        
        shadow_size_scaled = shadow_size * scale
        shadow_blur_scaled = shadow_blur * scale
        shadow_offset_scaled = shadow_offset * scale
        container_size_scaled = container_size * scale
        
        # Create a shadow canvas
        shadow_canvas_large = Image.new("RGBA", (shadow_size_scaled, shadow_size_scaled), (0, 0, 0, 0))
        shadow_draw_large = ImageDraw.Draw(shadow_canvas_large)
        
        # Draw the shadow shape (black with opacity)
        shadow_color = (0, 0, 0, 100) # Semi-transparent black
        shadow_shape_pos = (shadow_blur_scaled + shadow_offset_scaled, shadow_blur_scaled + shadow_offset_scaled, 
                            shadow_blur_scaled + shadow_offset_scaled + container_size_scaled, shadow_blur_scaled + shadow_offset_scaled + container_size_scaled)
        
        if shape == 'circle':
            shadow_draw_large.ellipse(shadow_shape_pos, fill=shadow_color)
        elif shape == 'rounded_square':
            radius = int(container_size_scaled * 0.25)
            shadow_draw_large.rounded_rectangle(shadow_shape_pos, radius=radius, fill=shadow_color)
        else:  # square
            shadow_draw_large.rectangle(shadow_shape_pos, fill=shadow_color)
            
        # Blur the shadow
        shadow_canvas_large = shadow_canvas_large.filter(ImageFilter.GaussianBlur(shadow_blur_scaled))
        shadow_canvas = shadow_canvas_large.resize((shadow_size, shadow_size), Image.Resampling.LANCZOS)
        
        # Paste container onto shadow canvas
        shadow_canvas.paste(container, (shadow_blur, shadow_blur), mask=container)
        return shadow_canvas, shadow_blur
        
    return container, 0

def generate_qr_code(
    url,
    fill_color="#000000",
    back_color="#FFFFFF",
    module_style="classic",
    eye_style="classic",
    logo_file=None,
    logo_size_pct=20,
    logo_shape="circle",
    has_logo_border=True,
    has_logo_shadow=True,
    border_size=4,
    box_size=10,
    error_correction="H",
    transparent_background=False,
    gradient_type="solid",
    gradient_color="#3B82F6"
):
    # 1. Validation
    if not url or not url.strip():
        raise ValueError("URL cannot be empty.")
        
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("Invalid target URL. Make sure it starts with http:// or https://")
        
    if logo_file:
        try:
            # We open the image and run verify() to check for corruption
            if isinstance(logo_file, str):
                logo_img = Image.open(logo_file)
            else:
                logo_img = Image.open(logo_file)
            logo_img.verify()
            
            # Reopen the file since verify() invalidates the file pointer/stream
            if isinstance(logo_file, str):
                logo_img = Image.open(logo_file)
            else:
                logo_file.seek(0)
                logo_img = Image.open(logo_file)
        except Exception:
            raise ValueError("Corrupted or unsupported logo image format.")
            
    # Determine error correction level
    ec_levels = {
        'L': qrcode.constants.ERROR_CORRECT_L,
        'M': qrcode.constants.ERROR_CORRECT_M,
        'Q': qrcode.constants.ERROR_CORRECT_Q,
        'H': qrcode.constants.ERROR_CORRECT_H,
    }
    ec_level = ec_levels.get(error_correction, qrcode.constants.ERROR_CORRECT_H)
    
    # Configure QR code
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec_level,
        box_size=box_size,
        border=border_size,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Parse colors
    back_rgb = hex_to_rgb(back_color)
    fill_rgb = hex_to_rgb(fill_color)
    gradient_rgb = hex_to_rgb(gradient_color)
    
    # Get styles
    mod_drawer = get_module_drawer(module_style)
    eye_dr = get_eye_drawer(eye_style)
    color_mask = get_color_mask(gradient_type, back_rgb, fill_rgb, gradient_rgb)
    
    # Generate QR image as RGB
    qr_img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=mod_drawer,
        eye_drawer=eye_dr,
        color_mask=color_mask
    ).convert("RGB")
    
    qr_width, qr_height = qr_img.size
    
    # 2. Key out background color first (if transparent background is enabled)
    # This ensures that any background-matching colors inside the logo are NOT keyed out later!
    if transparent_background:
        qr_img = qr_img.convert("RGBA")
        datas = qr_img.getdata()
        newData = []
        for item in datas:
            # If the pixel matches the background color exactly, make it transparent
            if item[0:3] == back_rgb:
                newData.append((0, 0, 0, 0))
            else:
                newData.append(item)
        qr_img.putdata(newData)
        
    # 3. Embed logo if provided
    if logo_file:
        try:
            # Reopen logo image
            if isinstance(logo_file, str):
                logo_img = Image.open(logo_file)
            else:
                logo_file.seek(0)
                logo_img = Image.open(logo_file)
                
            # Validate logo size bounds
            if logo_size_pct < 10 or logo_size_pct > 30:
                logo_size_pct = 20
                
            # Calculate size of the logo in pixels
            logo_max_size = int(qr_width * (logo_size_pct / 100.0))
            
            # Process logo (shape, border, shadow)
            logo_processed, shadow_blur = process_logo(
                logo_img=logo_img,
                size=logo_max_size,
                shape=logo_shape,
                has_border=has_logo_border,
                has_shadow=has_logo_shadow
            )
            
            # Paste logo into center of QR code
            processed_width, processed_height = logo_processed.size
            pos_x = (qr_width - processed_width) // 2
            pos_y = (qr_height - processed_height) // 2
            
            # Convert base QR image to RGBA if not already (for blending logo transparency)
            qr_img = qr_img.convert("RGBA")
            qr_img.paste(logo_processed, (pos_x, pos_y), mask=logo_processed)
            
        except Exception as e:
            # Re-raise the error so the app receives it
            raise ValueError(f"Failed to process and embed logo: {str(e)}")
            
    # Return the final image (retaining RGBA/RGB mode without forced conversion to RGB)
    return qr_img

