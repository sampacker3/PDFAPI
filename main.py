# main.py - PDF API using pdfkit
from flask import Flask, request, jsonify
import pdfkit
import base64
import tempfile
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure pdfkit options for better PDF output
PDF_OPTIONS = {
    'page-size': 'A4',
    'margin-top': '0.75in',
    'margin-right': '0.75in',
    'margin-bottom': '0.75in',
    'margin-left': '0.75in',
    'encoding': "UTF-8",
    'no-outline': None,
    'enable-local-file-access': None
}

# Test pdfkit on startup
logger.info("🔥 Testing pdfkit...")
try:
    test_html = "<html><body><h1>Test</h1></body></html>"
    pdf_bytes = pdfkit.from_string(test_html, False, options=PDF_OPTIONS)
    logger.info(f"✅ pdfkit test successful - Generated {len(pdf_bytes)} bytes")
except Exception as e:
    logger.error(f"❌ pdfkit test failed: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'pdfkit-api',
        'version': '1.0.0'
    })

@app.route('/convert', methods=['POST', 'OPTIONS'])
def convert():
    """Convert HTML to PDF using pdfkit"""
    
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
        
        # Add basic styling if none exists
        if '<style>' not in html_content.lower() and 'stylesheet' not in html_content.lower():
            styled_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>PDF Document</title>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 0; 
                        padding: 20px; 
                        line-height: 1.6; 
                        color: #333;
                    }}
                    h1 {{ 
                        color: #2c3e50; 
                        border-bottom: 2px solid #3498db; 
                        padding-bottom: 10px; 
                    }}
                    h2 {{ color: #34495e; margin-top: 30px; }}
                    h3 {{ color: #7f8c8d; }}
                    table {{ 
                        border-collapse: collapse; 
                        width: 100%; 
                        margin: 20px 0; 
                    }}
                    th, td {{ 
                        border: 1px solid #ddd; 
                        padding: 12px; 
                        text-align: left; 
                    }}
                    th {{ 
                        background-color: #f8f9fa; 
                        font-weight: bold; 
                    }}
                    tr:nth-child(even) {{ background-color: #f8f9fa; }}
                    ul, ol {{ margin: 15px 0; }}
                    li {{ margin-bottom: 5px; }}
                    blockquote {{
                        border-left: 4px solid #3498db;
                        margin: 20px 0;
                        padding-left: 20px;
                        font-style: italic;
                    }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
        else:
            styled_html = html_content
        
        # Generate PDF using pdfkit
        logger.info("Generating PDF with pdfkit...")
        pdf_bytes = pdfkit.from_string(styled_html, False, options=PDF_OPTIONS)
        
        if not pdf_bytes:
            raise Exception("PDF generation returned empty result")
        
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
        
        response = jsonify({
            'success': False,
            'error': str(e),
            'request_id': request_id,
            'processing_time_ms': round(processing_time, 2),
            'api_response_time_ms': round(processing_time, 2)
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/', methods=['GET'])
def root():
    """Root endpoint"""
    return jsonify({
        'service': 'PDFKit API',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': {
            'health': 'GET /health',
            'convert': 'POST /convert'
        }
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
