from flask import Flask, request, send_file, jsonify
from weasyprint import HTML
import io
import traceback

app = Flask(__name__)

@app.route("/convert", methods=["POST"])
def convert():
    try:
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
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    # debug=True so Flask will show errors
    app.run(host="0.0.0.0", port=8080, debug=True)
