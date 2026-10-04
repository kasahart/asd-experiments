# /// script
# requires-python = ">=3.10"
# dependencies = ["marimo==0.25.1"]
# ///
# Code and text: MIT. Dataset-derived figures and audio: CC BY-NC-SA 4.0.
# See docs/DATA_ATTRIBUTION.md and the original third-party LICENSE/NOTICE.
import marimo

__generated_with = "0.25.1"
app = marimo.App(width="medium", app_title="異常音検知：B0・B1・W1・SS")

@app.cell
def _():
    import marimo as mo
    import csv
    from decimal import Decimal
    from pathlib import Path
    from io import BytesIO
    ROOT = Path(__file__).resolve().parents[1]
    ASSETS = ROOT / "apps/assets/02"
    CONDITIONS = ("b0", "b1", "w1", "ss")
    def read_csv(name):
        with (ROOT / "results" / name).open(newline="") as source:
            return list(csv.DictReader(source))
    return ASSETS, BytesIO, CONDITIONS, Decimal, ROOT, mo, read_csv


@app.cell
def _(mo):
    mo.md('# ノイズ除去で、異常検知は良くなるか？ — 第2回の実験を読む\n\n[Zenn第1回](https://zenn.dev/kasahart/articles/kasahart-20260919-dcase2026-asd-01)の続きです。記事では、**同じ検知器に渡す音だけを変えたとき、成績がどう変わるか**を比較しました。このアプリでは結果の表を読み、実録音の図で2種類の引き算の違いを確かめます。\n\n**ブラウザーで結果・図・音を確認できます。** インストールやデータ・重みの取得は不要です。3節の再生ボタンから、各条件の全長6秒を試聴できます。音量は端末側で調整してください。\n\n保存済みの結果を読むアプリです。ここで推論や再採点は行いません。数値は既存の実行記録であり、この画面の表示による独立追試ではありません。\n\n## 1. 4条件で何を変えたか\n\n| 記号 | 記事での呼び方 | 検知器に渡す音 |\n|---|---|---|\n| B0 | 近いマイクのみ | 近いマイクの録音をそのまま使う。比較の基準 |\n| B1 | 遠いマイクのみ | 遠いマイクの録音をそのまま使う |\n| W1 | 線形減算（複素減算） | 遠い側の大きさと位相を調整して、近い側から引く |\n| SS | スペクトル減算 | 周波数ごとの大きさを引き、近い側の位相で波形へ戻す |\n\nどの条件もBEATs・RDP・BEAM・VarMinの設定は共通です。**正常音の比較基準も、それぞれの条件で作り直します。**\n\n')
    return

@app.cell
def _(mo):
    mo.md('## 2. 結果の読み方 — W1は上がり、SSは総合では上がらなかった\n\n次の表の「総合スコア」は記事の検証スコアと同じものです。高いほど良く、「B0との差」は近いマイクのみを基準にした**ポイント差**です。')
    return

@app.cell
def _(CONDITIONS, Decimal, mo, read_csv):
    _rows = {row["condition"]: row for row in read_csv("02-summary.csv")}
    _base = Decimal(_rows["b0"]["official_score"]) * 100
    _lines = ["| 条件 | 総合スコア | B0との差（ポイント） |", "|---|---:|---:|"]
    for _c in CONDITIONS:
        _score = Decimal(_rows[_c]["official_score"]) * 100
        _lines.append(f"| {_c.upper()} | {_score:.3f} | {_score - _base:+.3f} |")
    mo.md("\n".join(_lines))
    return

@app.cell
def _(mo):
    mo.md('**この比較では、W1はB0より高く、SSは低い結果です。** 遠いマイクを使えば必ず改善するわけではなく、使い方で結果が変わりました。\n\n### 機種ごとの結果も見る\n\npAUCは、正常音への誤警報を少なく抑えた範囲で、異常を見分ける成績です。表と棒グラフはpAUCを100倍し、0〜100で示しています。グラフの機種名は配布データの英語名です。日本語との対応は表に示します。')
    return

@app.cell
def _(CONDITIONS, Decimal, mo, read_csv):
    _names = {"BlowerDustCollector": "集じん機（BlowerDustCollector）", "Sander": "研磨機（Sander）", "SewingMachine": "ミシン（SewingMachine）", "ToothBrush": "電動歯ブラシ（ToothBrush）", "ToyDrone": "小型ドローン（ToyDrone）"}
    _values = {(r["machine"], r["condition"]): Decimal(r["pauc"]) * 100 for r in read_csv("02-by-machine.csv")}
    _lines = ["| 機種 | B0 | B1 | W1 | SS |", "|---|---:|---:|---:|---:|"]
    for _machine, _label in _names.items():
        _lines.append("| " + _label + " | " + " | ".join(f"{_values[_machine, c]:.3f}" for c in CONDITIONS) + " |")
    mo.md("\n".join(_lines))
    return

@app.cell
def _(ASSETS, mo):
    mo.image((ASSETS / "machine-pauc.png").read_bytes(), alt="機種別の4条件のpAUC", width=900)
    return

@app.cell
def _(mo):
    mo.md('## 3. 同じ実録音で波形を比較する\n\n使用する音源は、[DCASE 2026 Challenge Task 2 Additional Training Dataset v1](https://zenodo.org/records/20151556)に含まれる**電動歯ブラシ（ToothBrush）の正常動作の実録音**です。\n\n| 項目 | 使用する音源 |\n|---|---|\n| ファイル | `ToothBrush/train/section_00_source_train_normal_0000_noAttribute.wav` |\n| 区分 | section 00・sourceドメイン・正常訓練データ |\n| 長さ・形式 | 6秒・16 kHz・2チャンネル |\n| ch 0 | 機械に近いマイクの録音（B0） |\n| ch 1 | 機械から遠いマイクの同時録音（B1） |\n\n両マイクに機械音と環境音が混ざっています。遠方側も雑音だけの録音ではありません。同じ録音から、近接・遠方をそのまま使う場合と、遠方を参照して近接を処理する場合を比べます。\n\nW1は遠方の複素スペクトルを調整して近接から引き、SSはスペクトルの大きさを引きます。処理は実験と同じ関数です。\n\n対象録音の全6秒を処理しています。振幅軸・周波数軸・スペクトルのレベル軸・色範囲は4条件共通です。手動試聴では4条件すべて全長6秒の音声を再生します。\n\n各WAVは既存プレーヤーと同じPCM16・16 kHz・モノラル音声です。個別の正規化は追加していません。\n\n実録音の波形・スペクトル図はWandas 0.8.0で作成した保存図です。再描画する場合は[波形処理の説明](https://github.com/kasahart/asd-experiments/blob/c7dbe58739621a518ae5e045bee50d93745bb508/src/asd_min/waveform.md)を参照してください。この波形比較にモデルの重みは不要です。\n\n音声データ（アプリ内の埋め込み音声を含む）と実録音由来の図の出典・利用条件は、[帰属情報](https://github.com/kasahart/asd-experiments/blob/c7dbe58739621a518ae5e045bee50d93745bb508/docs/DATA_ATTRIBUTION.md)を参照してください。\n')
    return

@app.cell
def _(mo):
    mo.md('### B0：近接マイク\n\n処理前の基準です。機械音と環境音が混ざった録音を、そのまま検知器へ渡します。')
    return

@app.cell
def _(ASSETS, BytesIO, ROOT, mo):
    mo.vstack([
        mo.image((ASSETS / "b0.png").read_bytes(), alt="B0：全6秒の波形・スペクトログラム・スペクトル", width=900),
        mo.audio(BytesIO((ROOT / "audio/02-toothbrush/b0.wav").read_bytes()), normalize=False),
    ])
    return

@app.cell
def _(mo):
    mo.md('### B1：遠方マイク\n\n同時刻の遠方側です。近接側との波形・周波数成分の違いを見ます。遠方にも機械音が入るため、雑音だけの参照ではありません。')
    return

@app.cell
def _(ASSETS, BytesIO, ROOT, mo):
    mo.vstack([
        mo.image((ASSETS / "b1.png").read_bytes(), alt="B1：全6秒の波形・スペクトログラム・スペクトル", width=900),
        mo.audio(BytesIO((ROOT / "audio/02-toothbrush/b1.wav").read_bytes()), normalize=False),
    ])
    return

@app.cell
def _(mo):
    mo.md('### W1：線形減算（複素減算）\n\n対象録音の全6秒から周波数ごとの複素係数を求め、遠方に共通する成分を近接から引いた出力です。B0と同じ振幅軸で、残った波形と周波数成分を確認できます。')
    return

@app.cell
def _(ASSETS, BytesIO, ROOT, mo):
    mo.vstack([
        mo.image((ASSETS / "w1.png").read_bytes(), alt="W1：全6秒の波形・スペクトログラム・スペクトル", width=900),
        mo.audio(BytesIO((ROOT / "audio/02-toothbrush/w1.wav").read_bytes()), normalize=False),
    ])
    return

@app.cell
def _(mo):
    mo.md('### SS：スペクトル減算\n\n遠方の大きさを近接から引き、近接の位相を使った出力です。W1とは引き方が異なります。両者を同じ表示条件で比べます。')
    return

@app.cell
def _(ASSETS, BytesIO, ROOT, mo):
    mo.vstack([
        mo.image((ASSETS / "ss.png").read_bytes(), alt="SS：全6秒の波形・スペクトログラム・スペクトル", width=900),
        mo.audio(BytesIO((ROOT / "audio/02-toothbrush/ss.wav").read_bytes()), normalize=False),
    ])
    return

@app.cell
def _(mo):
    mo.md('### 4条件のパワースペクトルを重ねて比較する\n\n全長6秒からWelch平均したスペクトルを同じ軸に重ねます。レベルは共通の基準でdB表示し、個別に正規化しません。Wandasの`welch()`は振幅スペクトルを返しますが、そのdB値は振幅を二乗したパワーのdB値と同じです（PSD／Hzではありません）。帯域ごとの変化を見る図であり、機械音と雑音の内訳を示すものではありません。')
    return

@app.cell
def _(ASSETS, mo):
    mo.image((ASSETS / "spectrum.png").read_bytes(), alt="全6秒の4条件のパワースペクトル重ね描き", width=900)
    return

@app.cell
def _(mo):
    mo.md('## 4. 図と検知スコアの読み分け\n\nこの録音には機械音だけの正解波形がありません。振幅や帯域の変化は観察できますが、機械音の保持率や雑音除去の成功率には換算できません。上の検知スコアはデータ集合全体の評価で、この1録音の見た目や聞こえ方の順位ではありません。\n\n表示用STFTは可視化ライブラリWandasの処理です。W1・SSの計算用STFTは実験実装に固定してあり、表示から再計算しません。\n\n[波形処理の説明](https://github.com/kasahart/asd-experiments/blob/c7dbe58739621a518ae5e045bee50d93745bb508/src/asd_min/waveform.md) / [必要入力](https://github.com/kasahart/asd-experiments/blob/c7dbe58739621a518ae5e045bee50d93745bb508/docs/02-inputs.md)\n')
    return

@app.cell
def _(mo):
    mo.md('[再現用CLIとコード](https://github.com/kasahart/asd-experiments/blob/c7dbe58739621a518ae5e045bee50d93745bb508/README.md) / [アプリの実行・更新](https://github.com/kasahart/asd-experiments/blob/c7dbe58739621a518ae5e045bee50d93745bb508/apps/README.md)')
    return

if __name__ == "__main__":
    app.run()
