# Metal Sheet AI Inspection System (MS-AIS)

AI-powered quality control and counting system for metal sheets using Meta's SAM-3 model.

## Features

- 🤖 **AI-Powered Detection**: Advanced metal sheet detection using SAM-3 (when available) or robust contour-based fallback
- 📹 **Multiple Input Sources**: Supports RTSP streams, USB cameras, and video files
- 📏 **Real-time Measurements**: Automatic dimension calculation with configurable calibration
- 🔍 **Quality Control**: Surface defect detection (scratches, dents, color variations)
- ⚡ **Motion Detection**: Smart triggering only when objects are stable
- 🎯 **High Performance**: Optimized for NVIDIA Jetson Orin Nano edge devices
- 📊 **Real-time UI**: Streamlit-based interface with live video and results
- 🔄 **Automatic Fallback**: Seamlessly switches between SAM-3 and OpenCV-based detection

## System Requirements

### Hardware
- **Recommended**: NVIDIA Jetson Orin Nano (8GB RAM) - **Fully Optimized**
- **Alternative**: Any system with CUDA-compatible GPU
- **CPU-only**: Possible but with reduced performance

#### Jetson Orin Nano Deployment
- 📋 **Setup Guide**: See `JETSON_SETUP.md` for detailed instructions
- 🚀 **Quick Deploy**: SSH to `lee@192.168.2.122` and run `./run_jetson.sh`
- ⚡ **Optimizations**: GPU acceleration, hardware video decoding, performance mode
- 📊 **Expected**: 15-30 FPS real-time processing

### Software
- Python 3.10+
- CUDA 12.0+ (for GPU acceleration)
- 8GB+ RAM

## Installation

1. **Clone the repository:**
   ```bash
   cd /path/to/your/project
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **SAM-3 Model Support:**
   - **Current Status**: SAM-3 is not yet available in the current transformers version
   - **Fallback**: System uses advanced contour-based detection with OpenCV
   - **Performance**: Fallback method provides reliable metal sheet detection
   - **Future**: When SAM-3 becomes available, the system will automatically switch
   
   - Optional: Login to Hugging Face for future SAM-3 features:
   ```bash
   huggingface-cli login
   ```

## Usage

### Running the Application

1. **Start the Streamlit app:**
   ```bash
   streamlit run app.py
   ```

2. **Open your browser** and navigate to `http://localhost:8501`

### Configuration

1. **Select Input Source:**
   - **Live Camera**: RTSP URL or USB camera index
   - **Video File**: Upload video for testing

2. **Set Calibration:**
   - Enter pixel-to-millimeter conversion ratio
   - Use the calibration tool for accurate measurements

3. **Adjust Detection Settings:**
   - Confidence threshold for detection sensitivity
   - Defect sensitivity for quality control

4. **Start Monitoring:**
   - Click "START Monitoring" to begin real-time detection
   - Results appear in real-time with visual overlays

## Project Structure

```
ms_aims_streamlit/
├── .streamlit/
│   └── config.toml         # Streamlit configuration
├── data/
│   ├── inputs/             # Sample videos for testing
│   ├── outputs_ng/         # Rejected images
│   └── outputs_ok/         # Approved images
├── models/
│   └── sam3/               # SAM-3 model checkpoints
├── src/
│   ├── __init__.py
│   ├── camera.py           # Video streaming and motion detection
│   ├── detector.py         # SAM-3 AI engine
│   ├── processing.py       # Image processing utilities
│   └── ui_components.py    # Streamlit UI components
├── app.py                  # Main application
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Key Components

### AI Detection Engine (`detector.py`)
- SAM-3 model integration
- Text-based prompting ("metal sheet")
- Instance segmentation and object counting
- Dimension calculation and defect detection

### Video Processing (`camera.py`)
- Multi-source video input (RTSP/USB/file)
- Threaded streaming for performance
- Motion detection for smart triggering
- Auto-reconnection for reliability

### Image Processing (`processing.py`)
- ROI (Region of Interest) management
- Calibration and dimension calculation
- Surface quality analysis
- Result logging and data export

### User Interface (`ui_components.py`)
- Real-time video display with overlays
- Configuration controls
- Results visualization
- System information dashboard

## Performance Optimization

### For Jetson Orin Nano:
- Model quantization enabled by default
- CUDA acceleration for OpenCV operations
- Reduced display resolution (640x480)
- Frame processing in separate threads

### For Development:
- Enable debug mode for detailed logging
- Use smaller video files for testing
- Monitor GPU memory usage

## Troubleshooting

### Common Issues

1. **Model Loading Error:**
   - Ensure Hugging Face authentication is set up
   - Check internet connection for model download
   - Verify CUDA availability for GPU acceleration

2. **Video Input Issues:**
   - Check camera permissions
   - Verify RTSP URL format
   - Ensure video file format is supported (MP4, AVI, MOV)

3. **Performance Issues:**
   - Reduce video resolution
   - Increase confidence threshold
   - Close other GPU-intensive applications

### Logs and Debugging

- Check console output for error messages
- Monitor GPU memory usage with `nvidia-smi`
- Enable debug logging by modifying logging level

## Configuration Options

### Detection Parameters
- **Confidence Threshold**: 0.0-1.0 (default: 0.5)
- **Mask Threshold**: 0.0-1.0 (default: 0.5)
- **Defect Sensitivity**: 0.0-1.0 (default: 0.1)

### Performance Parameters
- **Buffer Size**: Number of frames to buffer (default: 10)
- **Motion Threshold**: Motion detection sensitivity (default: 0.05)
- **Processing Interval**: Minimum time between detections (default: 1.0s)

## API Reference

### SAM3Engine
```python
detector = SAM3Engine(model_name="facebook/sam3")
detector.load_model()

# Detect metal sheets
results = detector.detect_sheets(image, "metal sheet")
```

### VideoStreamer
```python
streamer = VideoStreamer(buffer_size=10)
streamer.connect(rtsp_url, InputSource.RTSP)
streamer.start()

frame = streamer.get_frame()
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For technical support:
- Check the troubleshooting section
- Review system requirements
- Ensure all dependencies are properly installed

## Version History

- **v1.0.0**: Initial release with SAM-3 integration
- Real-time metal sheet detection and counting
- Quality control with defect detection
- Streamlit-based user interface
