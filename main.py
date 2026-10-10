from flask import Flask, request, render_template, send_file, g
from music21 import converter, environment, note
from pypdf import PdfReader
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import re
import secrets
import shutil
import sys

# MuseScoreの設定（music21のユーザー共通設定は書き換えない）
if sys.platform.startswith('linux'):
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
musescore_path = os.environ.get('MUSESCORE_PATH')
if not musescore_path:
    for candidate in (
        '/Applications/MuseScore 4.app/Contents/MacOS/mscore',
        shutil.which('mscore'),
        shutil.which('musescore'),
        shutil.which('mscore3'),
    ):
        if candidate and os.path.isfile(candidate):
            musescore_path = candidate
            break
if musescore_path:
    environment.Environment()['musescoreDirectPNGPath'] = musescore_path

# Flaskアプリの初期化
app = Flask(__name__)

# カタカナ変換用の辞書 (シャープ付きも追加)
katakana_pitch = {
    'C': 'ド', 'C#': 'ド♯', 'D': 'レ', 'D#': 'レ♯',
    'E': 'ミ', 'F': 'ファ', 'F#': 'ファ♯',
    'G': 'ソ', 'G#': 'ソ♯', 'A': 'ラ', 'A#': 'ラ♯',
    'B': 'シ'
}


def render_pdf(score, output_path):
    shutdown_error = False
    try:
        score.write('musicxml.pdf', fp=output_path, trimEdges=False)
    except OSError as error:
        # MuseScore 4.7.x on macOS may crash after completing the PDF.
        # https://github.com/musescore/MuseScore/issues/34445
        if sys.platform != 'darwin' or 'mutex lock failed: Invalid argument' not in str(error):
            raise
        shutdown_error = True

    pdf_data = output_path.read_bytes()
    if not pdf_data.startswith(b'%PDF-') or not pdf_data.rstrip().endswith(b'%%EOF'):
        raise ValueError('MuseScore did not produce a complete PDF')
    if not PdfReader(BytesIO(pdf_data), strict=True).pages:
        raise ValueError('MuseScore produced an empty PDF')
    if shutdown_error:
        app.logger.warning('MuseScore had a known shutdown error; the generated PDF was verified.')
    return pdf_data


# アップロード用HTMLページ
@app.route('/')
def index():
    g.csp_nonce = secrets.token_urlsafe(16)
    return render_template('index.html', csp_nonce=g.csp_nonce)

# アップロードされたABCファイルを処理するルート
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    # 安全なファイル名を生成
    safe_filename = re.sub(r'[^\w\-.]', '_', file.filename)
    uploads_dir = os.path.join(app.root_path, 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    try:
        # リクエストごとに分離し、以前の変換結果が混ざらないようにする。
        with TemporaryDirectory(prefix='score-', dir=uploads_dir) as work_dir:
            file_path = Path(work_dir) / safe_filename
            file.save(file_path)

            # ABCファイルを読み込み
            score = converter.parse(file_path)

            # 音符にカタカナの音程を付加
            for element in score.recurse().notes:
                if isinstance(element, note.Note):
                    pitch_name = element.pitch.name  # 調号を含む音名を取得
                    katakana_name = katakana_pitch.get(pitch_name, '')
                    element.addLyric(katakana_name)  # カタカナを歌詞として追加

            output_filename = safe_filename + '.pdf'
            pdf_data = render_pdf(score, Path(work_dir) / output_filename)

        return send_file(
            BytesIO(pdf_data),
            as_attachment=True,
            mimetype='application/pdf',
            download_name=output_filename
        )
    except Exception as e:
        app.logger.error(f"Error processing file: {e}")
        return "An error occurred while processing the file.", 500

# セキュリティヘッダーを追加
@app.after_request
def set_secure_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    csp = "default-src 'self'"
    if getattr(g, 'csp_nonce', None):
        csp += f"; style-src 'self' 'nonce-{g.csp_nonce}'; script-src 'self' 'nonce-{g.csp_nonce}'"
    response.headers['Content-Security-Policy'] = csp
    return response

# アプリケーションのエントリーポイント
if __name__ == "__main__":
    app.run(host=os.environ.get('HOST', '0.0.0.0'), port=int(os.environ.get('PORT', '5000')))

