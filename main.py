from flask import Flask, request, render_template, send_file, after_this_request
from music21 import converter, environment, note
import os
import re

# MuseScoreの設定
os.environ["QT_QPA_PLATFORM"] = "offscreen"
us = environment.UserSettings()
us['musescoreDirectPNGPath'] = '/usr/bin/mscore3'  # MuseScoreの正しいパスを設定

# Flaskアプリの初期化
app = Flask(__name__)

# カタカナ変換用の辞書 (シャープ付きも追加)
katakana_pitch = {
    'C': 'ド', 'C#': 'ド♯', 'D': 'レ', 'D#': 'レ♯',
    'E': 'ミ', 'F': 'ファ', 'F#': 'ファ♯',
    'G': 'ソ', 'G#': 'ソ♯', 'A': 'ラ', 'A#': 'ラ♯',
    'B': 'シ'
}

# アップロード用HTMLページ
@app.route('/')
def index():
    return render_template('index.html')

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
    uploads_dir = 'uploads'
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, safe_filename)
    file.save(file_path)

    try:
        # ABCファイルを読み込み
        score = converter.parse(file_path)

        # 音符にカタカナの音程を付加
        for element in score.recurse().notes:
            if isinstance(element, note.Note):
                pitch_name = element.pitch.name  # 調号を含む音名を取得
                katakana_name = katakana_pitch.get(pitch_name, '')
                element.addLyric(katakana_name)  # カタカナを歌詞として追加

        # PDFで出力
        output_filename = safe_filename + '.pdf'
        output_path = os.path.join(uploads_dir, output_filename)
        score.write('musicxml.pdf', fp=output_path)

        # PDFファイルを返す（ダウンロード後に削除）
        @after_this_request
        def remove_file(response):
            try:
                os.remove(file_path)
                os.remove(output_path)
            except Exception as e:
                app.logger.error(f"Failed to remove file: {e}")
            return response

        return send_file(
            output_path,
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
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
