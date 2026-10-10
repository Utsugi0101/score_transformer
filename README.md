# score_transformer
リンク：https://scoreconversion.net/
## 本プログラムについて
- abc譜を音名振りをした楽譜に変換する
### abc譜
- アルファベットで書かれた楽譜です
- 特にケルト音楽で書かれる記法です
- [the session](https://thesession.org/)から好きな曲を検索し、abc記法の楽譜をダウンロードしてください

## Macで使う

Python 3.12、[uv](https://docs.astral.sh/uv/) と MuseScore を使います。
このフォルダで初回のみ実行してください。

```bash
brew install --cask musescore
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
```

起動するには `start.command` をダブルクリックするか、次を実行します。

```bash
./start.command
```

起動後、ブラウザで <http://127.0.0.1:8888/> を開き、ABCファイルを選んで
「アップロードして変換」を押すと、音名付きのPDFをダウンロードできます。
[動作確認用のABCファイル](examples/scale.abc)も使えます。
停止するときは起動したターミナルで `Ctrl+C` を押してください。

MuseScore は `/Applications/MuseScore 4.app` または PATH から検出します。
別の場所にある場合は、実行ファイルを `MUSESCORE_PATH` で指定できます。
ポートを変更する場合は `PORT=8889 ./start.command` のように起動してください。
通常はこのMacからだけアクセスできる設定です。

MuseScore 4.7.x の macOS 版には、PDF生成後の終了時に落ちる
[既知の不具合](https://github.com/musescore/MuseScore/issues/34445)があります。
このエラーに限り、新しく生成されたPDFの構造とページを検証してから返します。
PDFが不完全な場合や、それ以外のエラーは変換失敗として扱います。
