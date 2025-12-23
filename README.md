# ダダサバイバー系ローグライクアクションRPG

## 実行環境の必要条件
* python >= 3.10
* pygame >= 2.1
* （任意）音声を使う場合：pygame.mixer が動く環境（通常はpygame同梱）
* （任意）フォント：`misaki_mincho.ttf`（スタート画面で使用）

---

## ゲームの概要
* 主人公こうかとんをキーボード操作で“ダダサバイバー”するローグライクアクションRPGです。
* 敵を倒してスコア（経験値）を稼ぎ、レベルアップしながらWaveを進めます。
* Waveをクリアするとラスボスが出現します。

### ゲームプレイイメージ
<img width="1645" height="979" alt="Image" src="https://github.com/user-attachments/assets/bb116424-b86a-43aa-ab6e-31156cfe4aec" />
<img width="1647" height="974" alt="Image" src="https://github.com/user-attachments/assets/f6d48b06-ded7-4751-9529-228ee446fb37" />

---

## ゲームの遊び方
* 敵を倒して経験値（スコア）を集め、レベルアップしていく
* `{w,a,s,d}` または `{↑,←,↓,→}` キーで移動できる
* Waveをすべてクリアするとラスボスが出る

---

## 操作方法（キー一覧）

| キー | 内容 |
|---|---|

| ↑ / ↓ / ← / → | 移動 |

---

## ゲームの実装

## ゲーム機能チャート構想
![Image](https://github.com/user-attachments/assets/298c986d-7624-4731-b5c6-da07fec713ba)

### 共通基本機能
* 背景画像と主人公キャラクターの描画
* 敵の種類：5種類
* 武器の種類：5種類

### 分担追加機能（例）
* 最初の画面（スタート画面）の実装
* 武器の実装
* 敵の実装
* 経験値＆Level（ゲージUI含む）の実装
* こうかとんの基本性能（HP/移動/ダメージ等）の実装
* 追加スキル（EMP / Gravity / Shield / 拡散ビーム 等）

---

## ルール・ゲーム仕様

### スコア（経験値）とレベル
* 本作では `score.value` を「スコア兼 経験値」として扱います。
* 画面左上に Level と経験値ゲージが表示されます。
  * Level は `int(score.value / 10)` で算出されます。
  * ゲージは `score.value % 10`（0〜9）の進捗を 10 段階で表示します。

### こうかとん（プレイヤー）
* HP は `bird.hp` で管理されます。
* 左下にHPバーが表示され、同時に `Level` も表示されます。
* 敵に接触するとHPが減り、赤いダメージエフェクトが一定時間表示されます。
* HP が 0 以下になるとゲームオーバーです。

### 敵
* 敵は一定間隔でスポーンし、こうかとんの位置へ追従します。
* `score.value` に応じて敵の見た目（wave）が変化します。
* 一定条件を満たすとラスボス戦に移行します。

### ラスボス（LastBoss）
* Wave進行条件を満たすと通常敵と武器演出が整理され、ラスボスが出現します。
* ラスボスは巨大な敵で、上からじりじり降りてきます。
* ラスボス戦では接触しても敵が消えず、継続的にダメージを受けます。

---

## 主人公

<img width="48" height="48" alt="Image" src="https://github.com/user-attachments/assets/d15d8d34-8f3b-4e22-9de3-13efd168bba8" />

---

## 武器の実装（5種）

### ボム
<img width="256" height="256" alt="Image" src="https://github.com/user-attachments/assets/93edba30-0b56-4e0f-a92a-04f5cebebabb" />

最初に自機キャラの中心にボムを配置する。一定時間後、`Explosion` クラスを使い爆破エフェクトを発生させる。  
この爆発エフェクトに触れた敵はダメージを受ける。  
また、ボムに敵が衝突した場合は即座に起爆する。

### レーザー
<img width="1200" height="1200" alt="Image" src="https://github.com/user-attachments/assets/9464dd4d-f6b4-4b50-83b3-e6556ffc82af" />

自機キャラの角度に合わせてレーザーが射出される。直線上に移動し、敵と衝突してダメージを与えたあとも消失せず、敵を貫通する。  
一度の射出イベントで射出上限量に達した後、しばらくクールタイムが発生する。

### ミサイル
<img width="640" height="640" alt="Image" src="https://github.com/user-attachments/assets/5a9ba971-34c3-48cb-b9b9-e9bb4d60216f" />

一番近い敵をロックオンして射出され、そのターゲットが消失するか衝突するまで常にホーミングする。  
発射後はしばらくクールタイムが発生する。

### マシンガン
<img width="256" height="256" alt="Image" src="https://github.com/user-attachments/assets/3d221886-384b-48fd-8e79-f9e40d9507ec" />

自機キャラの角度に合わせて銃弾が射出される。直線状に移動し、敵と衝突した後、ダメージを与えて消失する。  
クールタイムが短く、連続的に弾丸を撃つことができる。

### 剣
<img width="1360" height="1360" alt="Image" src="https://github.com/user-attachments/assets/b34e68cd-aa47-4905-a598-4d808a81a8df" />

自機キャラのまわりを周回し、衝突時に敵にダメージを与える。  
一定時間顕現し、しばらくのクールタイムが発生したあとに再出現する。

---

## 敵の実装（5種 + シークレット）

### レポート
<img width="355" height="400" alt="Image" src="https://github.com/user-attachments/assets/9c76ff9e-fbdc-4381-b70f-f5daa339eeec" />

### 期限
<img width="375" height="400" alt="Image" src="https://github.com/user-attachments/assets/9eff35c3-96d8-466d-8a41-c1b7c006498c" />

### 生成AI
<img width="180" height="180" alt="Image" src="https://github.com/user-attachments/assets/93b147c3-a785-4a62-9725-2a9b24ff2f4d" />

### 警備員
<img width="412" height="450" alt="Image" src="https://github.com/user-attachments/assets/c862521f-ac6a-4a4c-a973-ead72b8a3064" />

### 教師
<img width="314" height="450" alt="Image" src="https://github.com/user-attachments/assets/c7172002-9391-4e49-8833-983c401a353e" />

### シークレット
すべてが謎に包まれている禁忌の存在。


---

## 依存ファイル（素材）

このゲームは `fig/` と `sound/` の素材を参照します。  
不足している場合、起動時にエラーになる可能性があります。

### 画像（例）
* `fig/back_ground.png`（背景）
* `fig/beam.png`（ビーム）
* `fig/bomb.png`（ボム）
* `fig/laser.png`（レーザー）
* `fig/missile.png`（ミサイル）
* `fig/bullet.png`（弾）
* `fig/sword.png`（剣）
* `fig/explosion.gif`（爆発）
* `fig/fantasy_maou_devil.png`（ラスボス）
* `fig/2.png`, `fig/serihu_pass_icon.png`（スタート画面装飾）
* `fig/3.png` など（こうかとん画像：番号png）

### フォント
* `misaki_mincho.ttf`（スタート画面で使用）

### 効果音（例）
* `sound/bb.wav`
* `sound/bb_effct.wav`
* `sound/gun.wav`
* `sound/laser.wav`
* `sound/mssle.wav`
* `sound/sword.wav`
* （任意）`fig/damage.mp3`（存在しない場合は無効化される）

---

## 実行方法

```bash
pip install pygame
python <ゲームファイル名>.py


