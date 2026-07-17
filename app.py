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
            response = jsonify({'success': False, 'message': 'URL cannot be empty.'})
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            return response, 400
            
        # Auto-prepend scheme if missing
        from urllib.parse import urlparse
        parsed = urlparse(url)
        if not parsed.scheme and ('.' in url or 'localhost' in url) and ' ' not in url:
            url = "http://" + url
            
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
        preset = request.form.get('preset', 'custom')
        
        # Check if logo file is uploaded
        logo_file = None
        if 'logo' in request.files:
            file = request.files['logo']
            if file.filename != '':
                # Read the file and validate size (2MB max)
                file_data = file.read()
                if len(file_data) > 2 * 1024 * 1024:
                    response = jsonify({'success': False, 'message': 'Uploaded logo exceeds the 2MB size limit.'})
                    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                    return response, 400
                logo_file = io.BytesIO(file_data)
                
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
        
        # Perform premium scale using Lanczos interpolation
        qr_img = qr_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            
        # Save to buffer as PNG (always PNG)
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        
        # Convert to base64
        base64_data = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
        
        # Determine descriptive filename
        if preset and preset != 'custom':
            filename = f"{preset}_qr.png"
        else:
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc.replace('www.', '').split('.')[0]
                if not domain:
                    domain = "qr_code"
                filename = f"{domain}_qr.png"
            except Exception:
                filename = "qr_code.png"
        
        response = jsonify({
            'success': True,
            'image': base64_data,
            'qr_data_url': f"data:image/png;base64,{base64_data}",
            'filename': filename,
            'mime': 'image/png'
        })
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response
        
    except ValueError as ve:
        response = jsonify({'success': False, 'message': str(ve)})
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response, 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        response = jsonify({'success': False, 'message': f"Server error during generation: {str(e)}"})
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        return response, 500

if __name__ == '__main__':
    # Render passes the PORT via environment variable; fall back to 5000 locally.
    # Must bind to 0.0.0.0 so Render can reach the service from the outside.
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'production') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
