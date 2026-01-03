# Star Trek - Python Edition

PC-8801版スタートレックをPythonで再現したテキストベース戦略ゲーム。
1978年のBASIC版（Mike Mayfield原作、Bob Leedom拡張）を忠実に再現。

## 実行方法

```bash
python3 startrek.py                # BEEPモード（デフォルト）
python3 startrek.py --sound off    # サウンドなし
python3 startrek.py --sound effects # 効果音あり（要pygame, numpy）
```

## ゲーム概要

- **目的**: 制限日数内に全クリンゴン艦を撃破
- **銀河構造**: 8×8クオドラント、各クオドラント内に8×8セクター
- **勝利条件**: 全クリンゴン撃破
- **敗北条件**: 時間切れ / エネルギー枯渇 / 艦破壊

## コマンド一覧

| コマンド | 機能 |
|----------|------|
| `NAV` | 航行（コース1-9、ワープ速度0-8） |
| `SRS` | 短距離センサー（現在クオドラント表示） |
| `LRS` | 長距離センサー（周囲9クオドラント情報） |
| `PHA` | フェーザー砲（エネルギー消費、自動照準） |
| `TOR` | 光子魚雷（方向指定、最大10発） |
| `SHE` | シールド（エネルギー配分） |
| `DAM` | 損害報告 |
| `COM` | コンピュータ（6機能） |
| `XXX` | ゲーム終了 |

## 重要な仕様

### 方向システム（NAV / TOR共通）

```
    4   3   2
      ↖ ↑ ↗
  5 ←   E   → 1
      ↙ ↓ ↘
    6   7   8
```

- 1-8の整数、または小数で中間方向も指定可能
- 9 = 1（360度で一周）

### LRS（長距離センサー）の読み方

```
3桁数字: KBS
  K = クリンゴン数  (百の位)
  B = スターベース数 (十の位)
  S = 星の数       (一の位)

例: 215 = クリンゴン2隻、スターベース1基、星5個
```

### シンボル

| シンボル | 意味 |
|----------|------|
| `<*>` | エンタープライズ号 |
| `+K+` | クリンゴン艦 |
| `>!<` | スターベース |
| ` * ` | 星（障害物） |
| ` . ` | 空白 |

---

## 戦闘計算式（オリジナルBASIC準拠）

### フェーザー攻撃

```python
# 距離計算（ユークリッド距離）
distance = sqrt((klingon_row - enterprise_row)² + (klingon_col - enterprise_col)²)

# ダメージ計算
energy_per_target = total_energy / number_of_klingons
damage = (energy_per_target / distance) * random(2.0 ~ 3.0)

# 撃破判定
if damage >= klingon_energy:
    # クリンゴン撃破
```

**特徴:**
- 距離が遠いほどダメージ減衰
- 乱数で2〜3倍の振れ幅
- エネルギーは敵数で均等分配（自動照準）

### フェーザー過熱

```python
if energy > 1500:
    overheat_chance = (energy - 1500) / 1500
    # overheat_chanceの確率でフェーザー損傷
```

### クリンゴン反撃

```python
damage = (klingon_energy / distance) * random(0.5 ~ 1.0)

# シールドが先にダメージ吸収
if shields >= damage:
    shields -= damage
else:
    remaining = damage - shields
    shields = 0
    energy -= remaining
    # 60%の確率でシステム損傷
```

### 光子魚雷

```python
# 方向から移動ベクトル計算
# 1ステップずつ移動し、最初にヒットした対象に命中
# 星に当たると吸収される
# クオドラント外に出るとミス
```

---

## リソース管理

| リソース | 初期値 | 回復方法 |
|----------|--------|----------|
| エネルギー | 3000 | スターベースでドッキング |
| 光子魚雷 | 10発 | スターベースでドッキング |
| シールド | 0 | エネルギーから配分（SHEコマンド） |

### ドッキング

- スターベースに隣接すると自動ドッキング
- エネルギー3000、魚雷10発に回復
- シールドは0にリセット
- DAMコマンドで全システム修理可能

---

## ファイル構成

```
startrek/
├── startrek.py           # エントリーポイント、ゲームループ
├── game/
│   ├── galaxy.py         # Galaxy, Quadrant, Sector, Klingonクラス
│   ├── enterprise.py     # Enterpriseクラス、リソース・ダメージ管理
│   ├── combat.py         # 戦闘計算（★オリジナル計算式）
│   └── commands.py       # コマンドハンドラ
├── ui/
│   ├── display.py        # 画面表示
│   └── sound.py          # サウンド（3モード対応）
├── data/
│   └── quadrant_names.py # クオドラント名（64個）
└── docs/
    └── startrek_spec.html # 詳細仕様書
```

### 各ファイルの役割

| ファイル | 修正が必要なケース |
|----------|-------------------|
| `combat.py` | ダメージ計算、戦闘バランス調整 |
| `commands.py` | コマンドの動作変更、新コマンド追加 |
| `galaxy.py` | マップ生成、敵配置ロジック |
| `enterprise.py` | 自機のリソース、システム損傷 |
| `display.py` | 画面レイアウト、表示形式 |
| `sound.py` | 効果音の追加・変更 |

---

## 実装時の注意点

### 1. EntityTypeの比較
```python
# 正しい
if entity == EntityType.KLINGON:

# 間違い（動作しない）
if entity.name == 'KLINGON':
```

### 2. 画面クリアのタイミング
情報表示系コマンド（LRS, COM, DAM, TOR, PHA）は結果表示後に
`wait_for_key()` でEnter待ちしてから画面クリア。

### 3. 方向計算
```python
# atan2で角度を計算し、1-9の方向に変換
angle = math.atan2(-dr, dc)  # -dr: 行は下向きに増加するため
direction = 1.0 + (angle * 4.0 / math.pi)
```

---

## サウンドシステム

| モード | 依存 | 説明 |
|--------|------|------|
| `OFF` | なし | サウンドなし |
| `BEEP` | なし | ターミナルBEEP（`\a`） |
| `EFFECTS` | pygame, numpy | 波形生成による効果音 |

### 効果音生成（EFFECTSモード）

```python
# フェーザー: 高周波→低周波スイープ
freq = np.linspace(2000, 500, samples)

# 爆発: ホワイトノイズ + 減衰
noise = np.random.uniform(-1, 1, samples)
wave = noise * np.exp(-t * 8)

# ワープ: 低周波→高周波上昇
freq = np.linspace(100, 1000, samples)
```

---

## 参考資料

- [詳細仕様書](docs/startrek_spec.html) - ブラウザで閲覧
- [Super Star Trek (1978 BASIC)](https://github.com/philspil66/Super-Star-Trek)
- [Star Trek Mania Wiki](https://startrek-mania.fandom.com/ja/wiki/スタートレック_(マイコンゲーム))

---

## ライセンス

オリジナルのBASIC版はパブリックドメイン。
このPython実装もMITライセンスとして公開。
