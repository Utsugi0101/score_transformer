from flask import Flask, request, render_template, send_file
from music21 import converter, environment, note
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

us = environment.UserSettings()
us['musescoreDirectPNGPath'] = '/usr/bin/musescore'



# Flaskアプリの初期化
app = Flask(__name__)



# MuseScoreのパスを設定
# us = environment.UserSettings()
# us['musescoreDirectPNGPath'] = '/Applications/MuseScore 4.app/Contents/MacOS/mscore'

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
@app.route('/api', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    
    # ファイルを保存する
    file_path = os.path.join('uploads', file.filename)
    file.save(file_path)

    # ABCファイルを読み込み
    score = converter.parse(file_path)

        # 音符にカタカナの音程を付加
    for element in score.recurse().notes:
        if isinstance(element, note.Note):
            pitch_name = element.pitch.name  # 調号を含む音名を取得
            katakana_name = katakana_pitch.get(pitch_name, '')
            if katakana_name:
                element.addLyric(katakana_name)  # カタカナを歌詞として追加



    # PDFで出力
    output_path = os.path.join('uploads', file.filename + '.pdf')
    score.write('musicxml.pdf', fp=output_path)


    # PDFファイルを返す
    return send_file(output_path, as_attachment=True)
if __name__ == '__main__':
    
    app.debug = True
    app.run(host='0.0.0.0', port=8888)