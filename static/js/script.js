/* QR Studio - Frontend Controller Logic */

document.addEventListener('DOMContentLoaded', () => {
    // Form and Interactive Inputs
    const form = document.getElementById('qr-form');
    const urlInput = document.getElementById('url');
    const fillPicker = document.getElementById('fill_color');
    const backPicker = document.getElementById('back_color');
    const gradientType = document.getElementById('gradient_type');
    const gradientPicker = document.getElementById('gradient_color');
    const gradientGroup = document.querySelector('.gradient-color-group');
    
    // Sliders & Toggles
    const logoSizeSlider = document.getElementById('logo_size');
    const logoSizeVal = document.getElementById('logo-size-val');
    const borderSlider = document.getElementById('border_size');
    const borderSizeVal = document.getElementById('border-size-val');
    
    // Accordion
    const accordionToggle = document.querySelector('.accordion-toggle');
    const accordionContent = document.querySelector('.accordion-content');
    
    // Drag & Drop / Upload
    const dropZone = document.getElementById('drop-zone');
    const logoInput = document.getElementById('logo');
    const logoPreviewContainer = document.getElementById('logo-preview-container');
    const logoThumbnail = document.getElementById('logo-thumbnail');
    const removeLogoBtn = document.getElementById('remove-logo-btn');
    
    // Preview & Action Buttons
    const placeholderState = document.getElementById('preview-placeholder');
    const imageState = document.getElementById('preview-image-container');
    const qrPreviewImg = document.getElementById('qr-preview-img');
    const previewLoader = document.getElementById('preview-loader');
    const actionControls = document.getElementById('action-controls');
    const downloadPngBtn = document.getElementById('download-png-btn');
    const copyImgBtn = document.getElementById('copy-img-btn');
    
    // Presets
    const presetBtns = document.querySelectorAll('.preset-btn');
    
    // State Tracking
    let uploadedFile = null;
    let qrImageDataUrl = null;
    let currentAbortController = null;
    let lastSerializedData = '';
    
    // Define Color Presets
    const presets = {
        portfolio: { fill: '#FFFFFF', back: '#FF7A00', gradient: 'solid' },
        linkedin: { fill: '#FFFFFF', back: '#0A66C2', gradient: 'solid' },
        github: { fill: '#FFFFFF', back: '#181717', gradient: 'solid' },
        custom: { fill: '#1A1A1A', back: '#FFFFFF', gradient: 'solid' }
    };

    /* --- Accordion Panel Toggle --- */
    accordionToggle.addEventListener('click', () => {
        accordionToggle.classList.toggle('open');
        accordionContent.classList.toggle('show');
    });

    /* --- Preset Selection --- */
    presetBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            presetBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            const presetName = btn.getAttribute('data-preset');
            const values = presets[presetName];
            
            if (values) {
                fillPicker.value = values.fill;
                backPicker.value = values.back;
                gradientType.value = values.gradient;
                
                // Trigger hex labels refresh
                updateHexLabel(fillPicker);
                updateHexLabel(backPicker);
                toggleGradientGroup();
                
                // Trigger preview refresh if URL is populated
                if (urlInput.value.trim() !== '') {
                    generateQRCode();
                }
            }
        });
    });

    // Helper: update text labels next to color picker
    function updateHexLabel(picker) {
        const wrapper = picker.closest('.color-picker-wrapper');
        if (wrapper) {
            const label = wrapper.querySelector('.hex-label');
            if (label) label.textContent = picker.value.toUpperCase();
        }
    }

    [fillPicker, backPicker, gradientPicker].forEach(picker => {
        picker.addEventListener('input', () => {
            updateHexLabel(picker);
            
            // Mark custom preset active since user is modifying colors manually
            presetBtns.forEach(b => b.classList.remove('active'));
            document.querySelector('[data-preset="custom"]').classList.add('active');
            
            if (urlInput.value.trim() !== '') {
                debounceGenerate();
            }
        });
    });

    /* --- Gradient Toggle --- */
    function toggleGradientGroup() {
        if (gradientType.value !== 'solid') {
            gradientGroup.classList.remove('hidden');
        } else {
            gradientGroup.classList.add('hidden');
        }
    }
    
    gradientType.addEventListener('change', () => {
        toggleGradientGroup();
        if (urlInput.value.trim() !== '') {
            generateQRCode();
        }
    });

    /* --- Sliders Input Events --- */
    logoSizeSlider.addEventListener('input', () => {
        logoSizeVal.textContent = `${logoSizeSlider.value}%`;
        if (urlInput.value.trim() !== '') debounceGenerate();
    });

    borderSlider.addEventListener('input', () => {
        borderSizeVal.textContent = borderSlider.value;
        if (urlInput.value.trim() !== '') debounceGenerate();
    });

    // Handle generic dropdown changes
    const selectElements = ['logo_shape', 'module_style', 'eye_style', 'error_correction', 'output_size'];
    selectElements.forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
            if (urlInput.value.trim() !== '') generateQRCode();
        });
    });

    // Handle checkboxes
    const checkboxes = ['logo_border', 'logo_shadow', 'transparent_background'];
    checkboxes.forEach(id => {
        document.getElementById(id).addEventListener('change', () => {
            if (urlInput.value.trim() !== '') generateQRCode();
        });
    });

    /* --- Drag & Drop Image Logic --- */
    // Click to upload
    dropZone.addEventListener('click', () => logoInput.click());
    
    // File Selected
    logoInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleLogoFile(e.target.files[0]);
        }
    });
    
    // Drag Events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleLogoFile(files[0]);
        }
    });

    // Remove Logo Button
    removeLogoBtn.addEventListener('click', () => {
        logoInput.value = '';
        uploadedFile = null;
        logoPreviewContainer.classList.add('hidden');
        dropZone.classList.remove('hidden');
        showToast('Logo removed');
        
        if (urlInput.value.trim() !== '') {
            generateQRCode();
        }
    });

    // Handle image file rendering and sizing check
    function handleLogoFile(file) {
        // Validate is an image
        if (!file.type.startsWith('image/')) {
            showToast('Please select a valid image file', 'error');
            return;
        }
        
        // Validate size (2MB limit)
        if (file.size > 2 * 1024 * 1024) {
            showToast('File size must be under 2MB', 'error');
            return;
        }
        
        uploadedFile = file;
        
        // Show file thumbnail
        const reader = new FileReader();
        reader.onload = (e) => {
            logoThumbnail.src = e.target.result;
            dropZone.classList.add('hidden');
            logoPreviewContainer.classList.remove('hidden');
            showToast('Logo loaded successfully');
            
            // Automatically regenerate QR code with the new logo
            if (urlInput.value.trim() !== '') {
                generateQRCode();
            }
        };
        reader.readAsDataURL(file);
    }

    /* --- Form Submission & Generation --- */
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const url = urlInput.value.trim();
        if (!url) {
            showToast('Target URL is required', 'error');
            urlInput.focus();
            return;
        }
        generateQRCode();
    });

    // Dynamic generation as URL is typed
    urlInput.addEventListener('input', () => {
        if (urlInput.value.trim() === '') {
            resetPreview();
            lastSerializedData = '';
        } else {
            debounceGenerate();
        }
    });

    // Reset preview to placeholder and disable buttons
    function resetPreview() {
        qrImageDataUrl = null;
        qrPreviewImg.src = '';
        placeholderState.classList.remove('hidden');
        imageState.classList.add('hidden');
        actionControls.classList.add('disabled-state');
    }

    // Debounce function to prevent overlapping fetch requests on fast input changes
    let debounceTimer;
    function debounceGenerate() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            generateQRCode();
        }, 300);
    }

    // Serialize all setting inputs to prevent duplicate rendering when values didn't change
    function getSerializedFormSettings() {
        const logoName = uploadedFile ? uploadedFile.name : (logoInput.files.length > 0 ? logoInput.files[0].name : '');
        return [
            urlInput.value.trim(),
            fillPicker.value,
            backPicker.value,
            gradientType.value,
            gradientPicker.value,
            logoSizeSlider.value,
            borderSlider.value,
            document.getElementById('logo_shape').value,
            document.getElementById('module_style').value,
            document.getElementById('eye_style').value,
            document.getElementById('error_correction').value,
            document.getElementById('output_size').value,
            document.getElementById('logo_border').checked,
            document.getElementById('logo_shadow').checked,
            document.getElementById('transparent_background').checked,
            logoName
        ].join('|');
    }

    // Ajax call to Flask backend API
    async function generateQRCode(isDownload = false) {
        const url = urlInput.value.trim();
        if (!url) {
            resetPreview();
            return null;
        }

        // Lazy updates logic: skip rendering if settings haven't changed
        const serialized = getSerializedFormSettings();
        if (!isDownload && serialized === lastSerializedData) {
            return null;
        }
        if (!isDownload) {
            lastSerializedData = serialized;
        }

        // Show loading state
        if (isDownload) {
            previewLoader.querySelector('.loader-text').textContent = 'Preparing High-Res Download...';
        } else {
            previewLoader.querySelector('.loader-text').textContent = 'Generating QR...';
        }
        previewLoader.classList.remove('hidden');
        document.getElementById('generate-btn').disabled = true;
        document.querySelector('.btn-spinner').classList.remove('hidden');

        // Construct Form Data
        const formData = new FormData();
        formData.append('url', url);
        formData.append('fill_color', fillPicker.value);
        formData.append('back_color', backPicker.value);
        formData.append('module_style', document.getElementById('module_style').value);
        formData.append('eye_style', document.getElementById('eye_style').value);
        formData.append('logo_size', logoSizeSlider.value);
        formData.append('logo_shape', document.getElementById('logo_shape').value);
        formData.append('logo_border', document.getElementById('logo_border').checked ? 'true' : 'false');
        formData.append('logo_shadow', document.getElementById('logo_shadow').checked ? 'true' : 'false');
        formData.append('border_size', borderSlider.value);
        formData.append('error_correction', document.getElementById('error_correction').value);
        formData.append('transparent_background', document.getElementById('transparent_background').checked ? 'true' : 'false');
        formData.append('gradient_type', gradientType.value);
        formData.append('gradient_color', gradientPicker.value);
        
        const activePreset = document.querySelector('.preset-btn.active');
        if (activePreset) {
            formData.append('preset', activePreset.getAttribute('data-preset'));
        }

        // Optimize Preview (512px) vs High-Res Download (User dropdown value)
        const sizeSelected = document.getElementById('output_size').value;
        formData.append('output_size', isDownload ? sizeSelected : '512');

        if (uploadedFile) {
            formData.append('logo', uploadedFile);
        } else if (logoInput.files.length > 0) {
            formData.append('logo', logoInput.files[0]);
        }

        try {
            // Cancel previous request if running (Prevent duplicate requests)
            if (currentAbortController) {
                currentAbortController.abort();
            }
            currentAbortController = new AbortController();
            const signal = currentAbortController.signal;

            const response = await fetch('/generate', {
                method: 'POST',
                body: formData,
                signal: signal
            });

            const data = await response.json();

            if (data.success && data.qr_data_url) {
                if (isDownload) {
                    return data;
                } else {
                    qrImageDataUrl = data.qr_data_url;
                    qrPreviewImg.src = data.qr_data_url;
                    
                    // Toggle preview displays
                    placeholderState.classList.add('hidden');
                    imageState.classList.remove('hidden');
                    actionControls.classList.remove('disabled-state');
                }
            } else {
                showToast(data.message || 'Failed to generate QR Code', 'error');
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                return null;
            }
            console.error('Error:', error);
            showToast('Connection to server failed', 'error');
        } finally {
            // Remove loading state
            previewLoader.classList.add('hidden');
            document.getElementById('generate-btn').disabled = false;
            document.querySelector('.btn-spinner').classList.add('hidden');
        }
        return null;
    }

    /* --- Download and Copy Actions --- */
    downloadPngBtn.addEventListener('click', async () => {
        if (!urlInput.value.trim()) return;
        
        try {
            // Generate the high-res QR code on-demand based on selected dropdown size
            const data = await generateQRCode(true);
            if (data && data.qr_data_url) {
                const link = document.createElement('a');
                link.href = data.qr_data_url;
                link.download = data.filename || 'qr_code.png';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showToast('PNG Downloaded!');
            }
        } catch (e) {
            console.error(e);
            showToast('Download failed', 'error');
        }
    });

    copyImgBtn.addEventListener('click', async () => {
        if (!qrImageDataUrl) return;
        
        try {
            // Convert data URI (base64) into a blob
            const res = await fetch(qrImageDataUrl);
            const blob = await res.blob();
            
            // Clipboard writes expect PNG format
            await navigator.clipboard.write([
                new ClipboardItem({
                    'image/png': blob
                })
            ]);
            showToast('Copied to clipboard!');
        } catch (err) {
            console.error('Copy failed:', err);
            showToast('Clipboard copy not supported or failed', 'error');
        }
    });

    // Form Reset Button
    const resetBtn = document.getElementById('reset-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', () => {
            form.reset();
            
            updateHexLabel(fillPicker);
            updateHexLabel(backPicker);
            updateHexLabel(gradientPicker);
            toggleGradientGroup();
            
            uploadedFile = null;
            logoInput.value = '';
            logoPreviewContainer.classList.add('hidden');
            dropZone.classList.remove('hidden');
            
            logoSizeVal.textContent = `${logoSizeSlider.value}%`;
            borderSizeVal.textContent = borderSlider.value;
            
            presetBtns.forEach(b => b.classList.remove('active'));
            document.querySelector('[data-preset="custom"]').classList.add('active');
            
            resetPreview();
            lastSerializedData = '';
            
            showToast('Form reset to default settings');
        });
    }

    /* --- Theme Toggle Switch --- */
    const themeToggleBtn = document.getElementById('theme-toggle');
    
    // System Theme Preference Detection
    function getSystemThemePreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            return 'light';
        }
        return 'dark';
    }

    // Load saved theme preference (default to system theme if none saved)
    const savedTheme = localStorage.getItem('theme') || getSystemThemePreference();
    setTheme(savedTheme);

    function setTheme(theme) {
        if (theme === 'light') {
            document.documentElement.setAttribute('data-theme', 'light');
            themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
            localStorage.setItem('theme', 'light');
        } else {
            document.documentElement.removeAttribute('data-theme');
            themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
            localStorage.setItem('theme', 'dark');
        }
    }
    
    themeToggleBtn.addEventListener('click', () => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        if (currentTheme === 'light') {
            setTheme('dark');
            showToast('Switched to Dark Theme');
        } else {
            setTheme('light');
            showToast('Switched to Light Theme');
        }
    });

    /* --- Keyboard Shortcuts --- */
    document.addEventListener('keydown', (e) => {
        // Ctrl + Enter: Generate QR code
        if (e.ctrlKey && e.key === 'Enter') {
            e.preventDefault();
            generateQRCode();
        }
        // Ctrl + D: Download QR code
        if (e.ctrlKey && e.key === 'd' && qrImageDataUrl) {
            e.preventDefault();
            downloadPngBtn.click();
        }
    });

    /* --- Toast Notification Helper --- */
    function showToast(message, type = 'success') {
        const toast = document.getElementById('toast');
        const toastMsg = document.getElementById('toast-message');
        const toastIcon = toast.querySelector('.toast-icon');
        
        toastMsg.textContent = message;
        
        if (type === 'error') {
            toast.classList.add('error');
            toastIcon.className = 'fa-solid fa-circle-exclamation toast-icon';
        } else {
            toast.classList.remove('error');
            toastIcon.className = 'fa-solid fa-circle-check toast-icon';
        }
        
        toast.classList.remove('hidden');
        
        clearTimeout(toast.timer);
        toast.timer = setTimeout(() => {
            toast.classList.add('hidden');
        }, 3000);
    }
    
    // Initialize labels
    updateHexLabel(fillPicker);
    updateHexLabel(backPicker);
    updateHexLabel(gradientPicker);
});
