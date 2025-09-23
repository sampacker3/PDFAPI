from flask import Flask, request, jsonify
from weasyprint import HTML
import base64
import os
from concurrent.futures import ThreadPoolExecutor
import time
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Pre-warm PDF engine on startup
logger.info("🔥 Warming up PDF engine...")
start_time = time.time()
try:
    HTML(string="<html><body><h1>Warmup Test</h1></body></html>").write_pdf("/tmp/warmup.pdf")
    os.remove("/tmp/warmup.pdf")
    logger.info(f"✅ PDF engine ready in {time.time() - start_time:.2f}s")
except Exception as e:
    logger.error(f"❌ Warmup failed: {e}")

# Thread pool for concurrent processing
executor = ThreadPoolExecutor(max_workers=4)

def generate_pdf_with_styling(html_content):
    """Generate PDF with enhanced styling"""
    from bs4 import BeautifulSoup
    
    # Add professional styling if no CSS exists
    soup = BeautifulSoup(html_content, 'html.parser')
    if not soup.find('style') and not soup.find('link', rel='stylesheet'):
        style_tag = soup.new_tag('style')
        style_tag.string = """
            @page {
                margin: 1in;
                @bottom-center {
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 9pt;
                    color: #666;
                }
            }
            body { 
                font-family: 'Helvetica', 'Arial', sans-serif;
                line-height: 1.6; 
                color: #333;
                font-size: 11pt;
            }
            h1 { 
                color: #2c3e50; 
                border-bottom: 2px solid #3498db;
                padding-bottom: 8px;
                font-size: 18pt;
            }
            h2 { 
                color: #34495e; 
                margin-top: 24pt;
                font-size: 14pt;
            }
            h3 { 
                color: #7f8c8d; 
                font-size: 12pt;
            }
            p { 
                margin-bottom: 8pt; 
                text-align: justify;
            }
            table { 
                border-collapse: collapse; 
                width: 100%; 
                margin: 12pt 0;
            }
            th, td { 
                border: 1px solid #ddd; 
                padding: 8pt; 
                text-align: left; 
                font-size: 10pt;
            }
            th { 
                background-color: #f8f9fa;
                font-weight: bold;
            }
            tr:nth-child(even) { background-color: #f8f9fa; }
            ul, ol { margin: 8pt 0; }
            li { margin-bottom: 4pt; }
            .page-break { page-break-before: always; }
            img { max-width: 100%; height: auto; }
            blockquote {
                border-left: 4px solid #3498db;
                margin: 12pt 0;
                padding-left: 12pt;
                font-style: italic;
            }
        """
        if soup.head:
            soup.head.append(style_tag)
        else:
            head_tag = soup.new_tag('head')
            head_tag.append(style_tag)
            soup.insert(0, head_tag)
        html_content = str(soup)
    
    return html_content

def process_pdf(html_content, request_id):
    """Process PDF in thread pool"""
    start = time.time()
    try:
        # Apply styling
        styled_html = generate_pdf_with_styling(html_content)
        
        # Generate PDF
        pdf_bytes = HTML(string=styled_html).write_pdf()
        processing_time = time.time() - start
        
        return {
            'success': True,
            'pdf_base64': base64.b64encode(pdf_bytes).decode('utf-8'),
            'size_bytes': len(pdf_bytes),
            'processing_time_ms': round(processing_time * 1000, 2),
            'request_id': request_id
        }
    except Exception as e:
        logger.error(f"PDF generation failed for {request_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'processing_time_ms': round((time.time() - start) * 1000, 2),
            'request_id': request_id
        }

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'saas-pdf-api',
        'version': '1.0.0'
    })

@app.route('/convert', methods=['POST', 'OPTIONS'])
def convert():
    """Convert HTML to PDF - Production ready"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    request_start = time.time()
    request_id = request.headers.get('X-Request-ID', f'req-{int(time.time()*1000)}')
    
    try:
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
        
        # Process in thread pool
        future = executor.submit(process_pdf, html_content, request_id)
        result = future.result(timeout=30)
        
        # Add API timing
        result['api_response_time_ms'] = round((time.time() - request_start) * 1000, 2)
        
        # Log success
        if result['success']:
            logger.info(f"✅ PDF: {request_id}, {result['size_bytes']} bytes, "
                       f"{result['processing_time_ms']}ms")
        
        # CORS headers
        response = jsonify(result)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        
    except Exception as e:
        logger.error(f"❌ API Error {request_id}: {str(e)}")
        response = jsonify({
            'success': False, 
            'error': f'Server error: {str(e)}',
            'request_id': request_id,
            'api_response_time_ms': round((time.time() - request_start) * 1000, 2)
        })
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response, 500

@app.route('/', methods=['GET'])
def root():
    """API info endpoint"""
    return jsonify({
        'service': 'SaaS PDF API',
        'status': 'running',
        'endpoints': {
            'convert': 'POST /convert',
            'health': 'GET /health'
        },
        'version': '1.0.0'
    })

if __name__ == '__main__':
    # Development server
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)
