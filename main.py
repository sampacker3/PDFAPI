# main.py - Clean PDF API with forced dependencies
from flask import Flask, request, jsonify
import base64
import io
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Import WeasyPrint with error handling
try:
    from weasyprint import HTML
    logger.info("✅ WeasyPrint imported successfully")
except ImportError as e:
    logger.error(f"❌ WeasyPrint import failed: {e}")
    raise

# Test WeasyPrint on startup with minimal HTML
logger.info("🔥 Testing WeasyPrint...")
try:
    test_html = "<html><body><p>Test</p></body></html>"
    pdf_buffer = io.BytesIO()
    HTML(string=test_html).write_pdf(target=pdf_buffer)
    pdf_size = len(pdf_buffer.getvalue())
    pdf_buffer.close()
    logger.info(f"✅ WeasyPrint test successful - Generated {pdf_size} bytes")
except Exception as e:
    logger.error(f"❌ WeasyPrint test failed: {e}")
    logger.error(f"Error type: {type(e).__name__}")
    import traceback
    logger.error(f"Full traceback: {traceback.format_exc()}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'pdf-api',
        'version': '2.0.0'
    })

@app.route('/convert', methods=['POST', 'OPTIONS'])
def convert():
    """Convert HTML to PDF"""
    
    # Handle CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    start_time = datetime.now()
    request_id = f'req-{int(start_time.timestamp() * 1000)}'
    
    try:
        # Get request data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'request_id': request_id
            }), 400
        
        html_content = data.get('html', '')
        if not html_content:
            return jsonify({
                'success': False,
                'error': 'No HTML content provided',
                'request_id': request_id
            }), 400
        
        logger.info(f"Processing request: {request_id}")
        
        # Ensure we have proper HTML structure
        if not html_content.strip().lower().startswith('<!doctype') and not html_content.strip().lower().startswith('<html'):
            html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>PDF Document</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        h1 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
        th {{ background-color: #f8f9fa; }}
    </style>
</head>
<body>
    {html_content}
</body>
</html>"""
        
        # Generate PDF - using exact same method as your working example
        logger.info("Creating PDF buffer...")
        pdf_buffer = io.BytesIO()
        
        logger.info("Calling HTML().write_pdf()...")
        HTML(string=html_content).write_pdf(target=pdf_buffer)
        
        logger.info("Getting PDF bytes...")
        pdf_bytes = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        logger.info(f"PDF generated successfully: {len(pdf_bytes)} bytes")
        
        # Convert to base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        # Calculate timing
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"✅ Success: {request_id}, {len(pdf_bytes)} bytes, {processing_time:.1f}ms")
        
        response = jsonify({
            'success': True,
            'pdf_base64': pdf_base64,
            'size_bytes': len(pdf_bytes),
            'processing_time_ms': round(processing_time, 2),
            'request_id': request_id,
            'api_response_time_ms': round(processing_time, 2)
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"❌ Error in {request_id}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        
        # Log detailed error info
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        
        response = jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__,
            'request_id': request_id,
            'processing_time_ms': round(processing_time, 2),
            'api_response_time_ms': round(processing_time, 2)
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/', methods=['GET'])
def root():
    return jsonify({
        'service': 'Clean PDF API',
        'status': 'running',
        'version': '2.0.0',
        'endpoints': {
            'health': 'GET /health',
            'convert': 'POST /convert'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
