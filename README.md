# ダダサバイバー系ローグライクアクションRPG



## 実行環境の必要条件
* python >= 3.10
* pygame >= 2.1
* 必要なものがあれば追記してください（非推奨）

## ゲームの概要
* 主人公こうかとんをキーボード操作でダダサバイバーするゲーム
### ゲームプレイイメージ
<img width="1645" height="979" alt="Image" src="https://github.com/user-attachments/assets/bb116424-b86a-43aa-ab6e-31156cfe4aec" />
<img width="1647" height="974" alt="Image" src="https://github.com/user-attachments/assets/f6d48b06-ded7-4751-9529-228ee446fb37" />

## ゲームの遊び方
* 敵を倒して経験値を集め、レベルアップしていく
* {w,a,s,d}または{↑,←,↓,→}キーで移動できる
* Waveをすべてクリアするとラスボスが出る

## ゲームの実装
## ゲーム機能チャート構想
![Image](https://github.com/user-attachments/assets/298c986d-7624-4731-b5c6-da07fec713ba)

### 共通基本機能
* 背景画像と主人公キャラクターの描画
* 敵の種類5種類
* 武器5種類
### 分担追加機能
* 最初の画面の実装
* 武器の実装
* 敵の実装
* スタート画面の実装
* 経験値＆Levelの実装
* こうかとんの基本性能の実装
### メモ
* 最後に学務課が出てくる
* マップの方を動かすことでマップを拡張する
### 主人公

<img width="48" height="48" alt="Image" src="https://github.com/user-attachments/assets/d15d8d34-8f3b-4e22-9de3-13efd168bba8" />

### 武器の実装
* **ボム**

<img width="256" height="256" alt="Image" src="https://github.com/user-attachments/assets/93edba30-0b56-4e0f-a92a-04f5cebebabb" />
最初に自機キャラの中心にボムを配置する ~~（衝突判定はなし）~~。
一定時間後、Explosionクラスを使い爆破エフェクトを発生させ、
この爆発エフェクトに触れた敵はダメージを受ける。また、このボムに敵が衝突したあと、即座に起爆する。

* **レーザー**

<img width="1200" height="1200" alt="Image" src="https://github.com/user-attachments/assets/9464dd4d-f6b4-4b50-83b3-e6556ffc82af" />
自機キャラの角度に合わせてレーザーが射出される。直線上に移動し、敵と衝突してダメージを与えたあとも消失せず、敵を貫通する。また、一度の射出イベントの射出上限量に達した後、しばらくクールタイムが発生する。

* **ミサイル**

<img width="640" height="640" alt="Image" src="https://github.com/user-attachments/assets/5a9ba971-34c3-48cb-b9b9-e9bb4d60216f" />
一番近い敵をロックオンして射出され、そのターゲットが消失するか衝突するまで常にホーミングする。一回発射した後はしばらくクールタイムが発生する。

* **マシンガン**

<img width="256" height="256" alt="Image" src="https://github.com/user-attachments/assets/3d221886-384b-48fd-8e79-f9e40d9507ec" />
自機キャラの角度に合わせて銃弾が射出される。直線状に移動し、敵と衝突した後、ダメージを与えて消失する。また、クールタイムが短いため、連続的に弾丸を撃つことができる。

* **剣**

<img width="1360" height="1360" alt="Image" src="https://github.com/user-attachments/assets/b34e68cd-aa47-4905-a598-4d808a81a8df" />
自機キャラのまわりをずっと周回し、衝突時に敵にダメージを与える。一定時間顕現し、しばらくのクールタイムが発生したあとに再出現する。

## 敵の実装
* **レポート**

<img width="355" height="400" alt="Image" src="https://github.com/user-attachments/assets/9c76ff9e-fbdc-4381-b70f-f5daa339eeec" />

* **期限**

<img width="375" height="400" alt="Image" src="https://github.com/user-attachments/assets/9eff35c3-96d8-466d-8a41-c1b7c006498c" />

* **生成AI**

<img width="180" height="180" alt="Image" src="https://github.com/user-attachments/assets/93b147c3-a785-4a62-9725-2a9b24ff2f4d" />

* **警備員**

<img width="412" height="450" alt="Image" src="https://github.com/user-attachments/assets/c862521f-ac6a-4a4c-a973-ead72b8a3064" />

* **教師**

<img width="314" height="450" alt="Image" src="https://github.com/user-attachments/assets/c7172002-9391-4e49-8833-983c401a353e" />

* **シークレット**

すべてが謎に包まれている禁忌の存在