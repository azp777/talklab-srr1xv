# -*- coding: utf-8 -*-
"""
婚活トークラボ ビルドスクリプト
konkatsu-app/data/ 内の JSON を読み込み、index.html のデータマーカー間を実データに差し替える。
- QUIZ:   quiz_sake.json, quiz_food.json, quiz_trip.json, quiz_life.json, quiz_love.json を結合
- SCENES: scenes_a.json, scenes_b.json を結合
- TECH:   tech.json
- NETA:   neta.json (オブジェクト)
データファイルが無いセクションはスキップ(警告のみ、エラーで落ちない)。
"""
import os
import json
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(BASE, "index.html")
DATA = os.path.join(BASE, "data")

# 文字化け対策: Windows コンソールでも UTF-8 で出力
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def warn(msg):
    print("[警告] " + msg)


def load_json(name):
    """data/name を読み込む。無ければ None。"""
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        warn("%s の読み込みに失敗: %s" % (name, e))
        return None


def load_array(files):
    """複数 JSON(配列)を結合。1つも無ければ None。"""
    out = []
    found = False
    for name in files:
        d = load_json(name)
        if d is None:
            warn("%s が見つかりません(スキップ)" % name)
            continue
        if not isinstance(d, list):
            warn("%s は配列ではありません(スキップ)" % name)
            continue
        out.extend(d)
        found = True
    return out if found else None


def js_dump(obj):
    """JSON を JS リテラル文字列として整形(1件1行)。
    配列は開始側の 'const XXX=[' が '[' を供給するため、ここでは '[' を付けない。"""
    if isinstance(obj, list):
        lines = [json.dumps(x, ensure_ascii=False) for x in obj]
        return "\n" + ",\n".join(lines) + "\n"
    # NETA: オブジェクト
    inner = []
    for k, v in obj.items():
        inner.append(json.dumps(k, ensure_ascii=False) + ":" + json.dumps(v, ensure_ascii=False))
    return "{" + ",\n".join(inner) + "\n"


def replace_section(html, start_token, end_marker, payload):
    """
    start_token(例 'const QUIZ=[')の開始位置から end_marker(例 '/*__QUIZ_END__*/')
    直前までを payload に置換する。文字列 index で堅牢に特定(正規表現不使用)。
    """
    si = html.find(start_token)
    if si < 0:
        warn("開始トークンが見つかりません: %s" % start_token)
        return html, False
    ei = html.find(end_marker, si)
    if ei < 0:
        warn("終了マーカーが見つかりません: %s" % end_marker)
        return html, False
    return html[:si] + start_token + payload + html[ei:], True


def main():
    if not os.path.exists(HTML):
        print("index.html が見つかりません: %s" % HTML)
        sys.exit(1)
    with open(HTML, encoding="utf-8") as f:
        html = f.read()

    summary = []

    # QUIZ
    quiz = load_array(["quiz_sake.json", "quiz_food.json", "quiz_trip.json",
                       "quiz_life.json", "quiz_love.json"])
    if quiz is not None:
        html, ok = replace_section(html, "const QUIZ=[", "/*__QUIZ_END__*/", js_dump(quiz))
        if ok:
            summary.append("クイズ: %d 問" % len(quiz))
    else:
        warn("クイズ用データが1つも無いためスキップ")

    # SCENES
    scenes = load_array(["scenes_a.json", "scenes_b.json"])
    if scenes is not None:
        html, ok = replace_section(html, "const SCENES=[", "/*__SCENES_END__*/", js_dump(scenes))
        if ok:
            summary.append("会話シーン: %d 本" % len(scenes))
    else:
        warn("シーン用データが1つも無いためスキップ")

    # TECH
    tech = load_json("tech.json")
    if tech is None:
        warn("tech.json が見つからないためスキップ")
    elif not isinstance(tech, list):
        warn("tech.json は配列ではありません(スキップ)")
    else:
        html, ok = replace_section(html, "const TECH=[", "/*__TECH_END__*/", js_dump(tech))
        if ok:
            summary.append("テクニック: %d 個" % len(tech))

    # NETA
    neta = load_json("neta.json")
    if neta is None:
        warn("neta.json が見つからないためスキップ")
    elif not isinstance(neta, dict):
        warn("neta.json はオブジェクトではありません(スキップ)")
    else:
        html, ok = replace_section(html, "const NETA=", "/*__NETA_END__*/", js_dump(neta))
        if ok:
            cnt = sum(len(v) for v in neta.values() if isinstance(v, list))
            summary.append("ネタ帳: %d 件" % cnt)

    with open(HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print("=" * 40)
    print("ビルド完了: index.html を更新しました")
    if summary:
        for s in summary:
            print("  ・" + s)
    else:
        print("  (差し替えたデータはありません。サンプルのままです)")
    print("=" * 40)


if __name__ == "__main__":
    main()
