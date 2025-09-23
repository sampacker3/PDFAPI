from flask import Flask, request, send_file, jsonify
from weasyprint import HTML
import io

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/convert", methods=["POST"])
def convert():
    data = request.get_json()
    if not data or "html" not in data:
        return jsonify({"error": "No HTML content provided"}), 400

    html_content = data["html"]
    pdf_bytes = HTML(string=html_content).write_pdf()

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name="output.pdf"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
