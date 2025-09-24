from flask import Flask, request, jsonify
from weasyprint import HTML
import base64
import io
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Test WeasyPrint on startup
logger.info("🔥 Testing PDF engine...")
try:
    pdf_buffer = io.BytesIO()
    HTML(string="<html><body><h1>Startup Test</h1></body></html>").write_pdf(target=pdf_buffer)
    pdf_buffer.close()
    logger.info("✅ PDF engine working correctly")
except Exception as e:
    logger.error(f"❌ PDF engine test failed: {e}")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'pdf-api',
        'version': '1.0.0'
    })

@app.route('/convert', methods=['POST', 'OPTIONS'])
def convert():
    """Convert HTML to PDF - Based on working example"""
    
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    start_time = datetime.now()
    request_id = f'req-{int(start_time.timestamp() * 1000)}'
    
    try:
        # Get JSON data
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON data provided',
                'request_id': request_id
            }), 400
        
        # Get HTML content
        html_content = data.get('html', '')
        if not html_content:
            return jsonify({
                'success': False,
                'error': 'No HTML content provided', 
                'request_id': request_id
            }), 400
        
        logger.info(f"Processing PDF request: {request_id}")
        
        # Add default styling if none exists
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
                        margin: 20px; 
                        line-height: 1.6; 
                        color: #333;
                    }}
                    h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 8px; }}
                    h2 {{ color: #34495e; margin-top: 24px; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f8f9fa; font-weight: bold; }}
                    tr:nth-child(even) {{ background-color: #f8f9fa; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
        else:
            styled_html = html_content
        
        # Generate PDF using working method from your example
        pdf_buffer = io.BytesIO()
        HTML(string=styled_html).write_pdf(target=pdf_buffer)
        
        # Get PDF bytes
        pdf_byte_string = pdf_buffer.getvalue()
        pdf_buffer.close()
        
        # Convert to base64 for JSON response
        pdf_base64 = base64.b64encode(pdf_byte_string).decode('utf-8')
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        logger.info(f"✅ PDF generated: {request_id}, {len(pdf_byte_string)} bytes, {processing_time:.1f}ms")
        
        # Return success response
        response = jsonify({
            'success': True,
            'pdf_base64': pdf_base64,
            'size_bytes': len(pdf_byte_string),
            'processing_time_ms': round(processing_time, 2),
            'request_id': request_id,
            'api_response_time_ms': round(processing_time, 2)
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"❌ Error processing {request_id}: {str(e)}")
        
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
    """Root endpoint info"""
    return jsonify({
        'service': 'PDF API',
        'status': 'running',
        'endpoints': {
            'health': 'GET /health',
            'convert': 'POST /convert'
        },
        'version': '1.0.0'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
