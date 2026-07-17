import os
import io
import base64
from flask import Flask, request, jsonify, render_template
from PIL import Image
from generator.qr_generator import generate_qr_code, hex_to_rgb

app = Flask(__name__)
# Enable maximum upload size (e.g. 16MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    try:
        # Retrieve form data
        url = request.form.get('url', '').strip()
        if not url:
            return jsonify({'success': False, 'error': 'URL cannot be empty.'}), 400
            
        fill_color = request.form.get('fill_color', '#000000')
        back_color = request.form.get('back_color', '#FFFFFF')
        module_style = request.form.get('module_style', 'classic')
        eye_style = request.form.get('eye_style', 'classic')
        
        logo_size_pct = int(request.form.get('logo_size', 20))
        logo_shape = request.form.get('logo_shape', 'circle')
        
        has_logo_border = request.form.get('logo_border', 'true') == 'true'
        has_logo_shadow = request.form.get('logo_shadow', 'true') == 'true'
        
        border_size = int(request.form.get('border_size', 4))
        output_size = request.form.get('output_size', '768')
        target_size = int(output_size)
        
        error_correction = request.form.get('error_correction', 'H')
        transparent_background = request.form.get('transparent_background', 'false') == 'true'
        
        gradient_type = request.form.get('gradient_type', 'solid')
        gradient_color = request.form.get('gradient_color', '#3B82F6')
        
        # Check if logo file is uploaded
        logo_file = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file.filename != '':
                # Read the file directly into a BytesIO stream
                logo_file = io.BytesIO(file.read())
                
        # Generate the QR Code
        qr_img = generate_qr_code(
            url=url,
            fill_color=fill_color,
            back_color=back_color,
            module_style=module_style,
            eye_style=eye_style,
            logo_file=logo_file,
            logo_size_pct=logo_size_pct,
            logo_shape=logo_shape,
            has_logo_border=has_logo_border,
            has_logo_shadow=has_logo_shadow,
            border_size=border_size,
            box_size=10,  # Default box size, we will resize later
            error_correction=error_correction,
            transparent_background=transparent_background,
            gradient_type=gradient_type,
            gradient_color=gradient_color
        )
        
        # Resize image to the exact requested output size
        # Preserve transparency mode (RGBA or RGB)
        is_rgba = transparent_background or qr_img.mode == "RGBA"
        
        if not is_rgba:
            # If JPEG/RGB, ensure we paste onto a solid background in case we had transparency
            if qr_img.mode == "RGBA":
                back_rgb = hex_to_rgb(back_color)
                background = Image.new("RGB", qr_img.size, back_rgb)
                background.paste(qr_img, mask=qr_img.split()[3])
                qr_img = background
            else:
                qr_img = qr_img.convert("RGB")
        
        # Perform premium scale using Lanczos interpolation
        qr_img = qr_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            
        # Save to buffer
        img_buffer = io.BytesIO()
        mime_type = "image/png" if is_rgba else "image/jpeg"
        qr_img.save(img_buffer, format="PNG" if is_rgba else "JPEG")
        img_buffer.seek(0)
        
        # Convert to base64
        base64_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'qr_data_url': f"data:{mime_type};base64,{base64_data}"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Running local server on port 5000
    app.run(debug=True, port=5000)
