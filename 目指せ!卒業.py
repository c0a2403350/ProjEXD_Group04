import math
import os
import random
import sys
import time
import pygame as pg


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)
        self.imgs = {
            (+1, 0): img,
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),
            (-1, 0): img0,
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 3
        self.state = "normal"
        self.hyper_life = 0

        self.hp = 10
        self.playerlv = 1

        # =========================
        # 機能：アイテム保持スロット（5枠）を実装
        # - item1〜item5 を「データ」として確実に保持できる形にする
        # - 外部から関数で安全に変更できるようにする
        # =========================
        # 1枠 = {"name": str, "attack": int, "level": int} or None
        self._items: list[dict | None] = [None] * 5

        # 互換用：既存コードの item1〜item5 を残す（中身は _items と同期）
        self.item1 = None
        self.item2 = None
        self.item3 = None
        self.item4 = None
        self.item5 = None

    # =========================
    # 機能：アイテム操作API（外部から呼ぶ用）
    # =========================
    def set_item(self, slot: int, name: str, attack: int = 0, level: int = 1) -> None:
        """
        指定スロット(1〜5)にアイテムをセットする
        """
        idx = slot - 1
        if idx < 0 or idx >= 5:
            raise ValueError("slot は 1〜5 で指定してください")

        self._items[idx] = {"name": name, "attack": int(attack), "level": int(level)}
        self._sync_item_aliases()

    def get_item(self, slot: int) -> dict | None:
        """
        指定スロット(1〜5)のアイテムを取得（無ければNone）
        """
        idx = slot - 1
        if idx < 0 or idx >= 5:
            raise ValueError("slot は 1〜5 で指定してください")
        return self._items[idx]

    def clear_item(self, slot: int) -> None:
        """
        指定スロット(1〜5)のアイテムを外す
        """
        idx = slot - 1
        if idx < 0 or idx >= 5:
            raise ValueError("slot は 1〜5 で指定してください")
        self._items[idx] = None
        self._sync_item_aliases()

    def swap_items(self, slot_a: int, slot_b: int) -> None:
        """
        スロット同士を入れ替える（1〜5）
        """
        ia = slot_a - 1
        ib = slot_b - 1
        if not (0 <= ia < 5 and 0 <= ib < 5):
            raise ValueError("slot は 1〜5 で指定してください")
        self._items[ia], self._items[ib] = self._items[ib], self._items[ia]
        self._sync_item_aliases()

    def get_items(self) -> list[dict | None]:
        """
        全スロットのコピーを返す（外部から直接書き換えされないようにする）
        """
        # dictの中身もコピーして返す
        out = []
        for it in self._items:
            out.append(None if it is None else dict(it))
        return out

    def _sync_item_aliases(self) -> None:
        """
        内部保持(_items)と互換変数(item1〜item5)を同期する
        """
        self.item1, self.item2, self.item3, self.item4, self.item5 = self._items

    # =========================
    # 互換：元の関数名を「ちゃんと動く形」にして残す（外部コードが呼んでもOK）
    # =========================
    def item_set_(self, item, attack, level):
        """
        機能：互換API
        - 旧仕様の item_set_ を「スロット1にセット」として扱う
        """
        self.set_item(1, str(item), attack, level)





    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]

            #加速イベント
            if key_lst[pg.K_LSHIFT]: #スペース
                self.speed = 20 #加速化処理
            else: #通常時
                self.speed = 10

        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]

        #追加機能4:無敵状態
        if self.state == "hyper":
            self.hyper_life -= 1
            self.image = pg.transform.laplacian(self.image)
            if self.hyper_life < 0:
                self.state = "normal"
                self.image = self.imgs[self.dire]

        screen.blit(self.image, self.rect)


class Bomb(pg.sprite.Sprite):
    """
    爆弾に関するクラス
    """
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (255, 0, 255), (0, 255, 255)
    ]

    def __init__(self, emy: "Enemy", bird: Bird):
        """
        爆弾円Surfaceを生成する
        引数1 emy：爆弾を投下する敵機
        引数2 bird：攻撃対象のこうかとん
        """
        super().__init__()
        self.state="active"
        rad = random.randint(10, 50)  # 爆弾円の半径：10以上50以下の乱数
        self.image = pg.Surface((2*rad, 2*rad))
        color = random.choice(__class__.colors)  # 爆弾円の色：クラス変数からランダム選択
        pg.draw.circle(self.image, color, (rad, rad), rad)
        self.image.set_colorkey((0, 0, 0))
        self.rect = self.image.get_rect()
        # 爆弾を投下するemyから見た攻撃対象のbirdの方向を計算
        self.vx, self.vy = calc_orientation(emy.rect, bird.rect)
        self.rect.centerx = emy.rect.centerx
        self.rect.centery = emy.rect.centery+emy.rect.height//2
        self.speed = 6

    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird,angle0=0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx))

        #機能６
        angle += angle0


        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()

class Gravity(pg.sprite.Sprite):
    """
    重力フィールドに関するクラス
    """
    def __init__(self, life: int):
        """
        イベント用のサーフェイスの定義
        引数：持続時間の整数型
        """
        super().__init__()
        self.life = life

        self.alpha = 250
        #イベント用サーフェイス
        self.image = pg.Surface((WIDTH, HEIGHT))
        pg.draw.rect(self.image, (0,0,0), (0,0,WIDTH,HEIGHT))
        self.image.set_alpha(self.alpha)

        self.rect = self.image.get_rect()

    def update(self):
        """
        時間処理
        """
        self.alpha -= 0.5
        pg.draw.rect(self.image, (0,0,0), (0,0,WIDTH,HEIGHT))
        self.image.set_alpha(self.alpha)

        self.life -= 1
        if self.life < 0:
            self.kill()

#機能６
class NeoBeam:
    def __init__(self,bird: Bird,num):
        """
        __init__ の Docstring

        :bird : こうかとん
        num : ビームの本数
        """
        self.bird = bird
        self.num = num
    def gen_beams(self):
        beams_list = []
        step = 100 // (self.num -1)
        for angle in range(-50,51,step):
            beams_list.append(Beam(self.bird,angle))
        return beams_list

class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bomb|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10 % 2]
        if self.life < 0:
            self.kill()


class Enemy(pg.sprite.Sprite):
    """
    Enemy の Docstring
    """

    def __init__(self):
        """
        Enemy の Docstring
        """
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/image.png"), 0, 0.1)
        self.rect = self.image.get_rect()
        #HP,attack,defense,speed
        self.stats = [100,100,100,2]
        if random.choice([True, False]):
            self.rect.centerx = random.choice([0, WIDTH])
            self.rect.centery = random.randint(0, HEIGHT)
        else:
            self.rect.centerx = random.randint(0, WIDTH)
            self.rect.centery = random.choice([0, HEIGHT])

        self.pos = pg.Vector2(self.rect.center)
        self.speed = self.stats[3]

    def update(self, bird_pos):
        target_vector = pg.math.Vector2(bird_pos)
        direction = target_vector - self.pos

        if direction.length() != 0:
            velocity  = direction.normalize() * self.speed
            self.pos += velocity
        self.rect.center = self.pos



class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 10000
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class EMP(pg.sprite.Sprite):
    """
    電磁パルス（EMP）に関するクラス
    """
    def __init__(self, emys: pg.sprite.Group, bombs: pg.sprite.Group, screen: pg.Surface):
        """
        EMPを生成し，敵機と爆弾を無効化する
        引数1 emys：敵機グループ
        引数2 bombs：爆弾グループ
        引数3 screen：画面Surface
        """
        super().__init__()
        self.emys = emys
        self.bombs = bombs
        self.screen = screen
        self.lifetime = 3#黄色画面表示時間

        # 敵機を無効化
        for emy in emys:
            emy.interval = float("inf")
            emy.image = pg.transform.laplacian(emy.image)

        # 爆弾を無効化
        for bomb in bombs:
            bomb.speed = bomb.speed // 2
            bomb.state = "inactive"

        # 画面全体に透明な黄色矩形を表示
        self.image = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        self.image.fill((255, 255, 0, 100))  # RGBA (alpha=100)
        self.rect = self.image.get_rect()

    def update(self):
        """
        EMP効果の継続時間を管理
        """
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.kill()


# ===================== ここから追加：Shieldクラス =====================

class Shield(pg.sprite.Sprite):
    """
    防御壁（Shield）に関するクラス
    青い矩形（横幅20 / 高さ こうかとんの身長の2倍）
    life フレーム経過で消滅
    """
    def __init__(self, bird: Bird, life: int):
        super().__init__()
        width = 20
        height = bird.rect.height * 2

        # 手順1：空のSurfaceを生成（アルファ付き）
        base_image = pg.Surface((width, height), pg.SRCALPHA)

        # 手順2：青いrectを描画
        pg.draw.rect(base_image, (0, 0, 255), (0, 0, width, height))

        # 手順3：こうかとんの向きを取得
        vx, vy = bird.dire
        if vx == 0 and vy == 0:
            vx = 1  # 万一(0,0)なら右向き扱い

        # 手順4：角度を求める
        angle = math.degrees(math.atan2(-vy, vx))

        # 手順5：Surfaceを回転
        self.image = pg.transform.rotozoom(base_image, angle, 1.0)

        # Rectを取得
        self.rect = self.image.get_rect()

        # 手順6：向いている方向に、こうかとん1体分ずらして配置
        offset = max(bird.rect.width, bird.rect.height)
        self.rect.centerx = bird.rect.centerx + vx * offset
        self.rect.centery = bird.rect.centery + vy * offset

        # 寿命
        self.life = life

    def update(self):
        """
        残り寿命を1減らし、0未満になったら消滅
        """
        self.life -= 1
        if self.life < 0:
            self.kill()

# ===================== ここまで追加：Shieldクラス =====================


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    bg_img = pg.image.load(f"fig/back_ground.png")
    bg_img = pg.transform.scale(bg_img, (WIDTH, HEIGHT))

    score = Score()

    bird = Bird(3, (900, 400))
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    gravity = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group()  # 防御壁グループ（1つだけ存在）
    emps = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        key_lst = pg.key.get_pressed()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                #機能６
                if key_lst[pg.K_LSHIFT]:
                    nb = NeoBeam(bird, 3) #第２引数がビームの本数
                    beams.add(nb.gen_beams())
                else:
                    


                    beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.value > 100:
                bird.state = "hyper"
                bird.hyper_life = 500
                score.value -= 100
            if event.type == pg.KEYDOWN and event.key== pg.K_e:
                if score.value >= 20:
                    emps.add(EMP(emys,bombs,screen))
                    score.value -=20
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                if score.value >= 200:
                    gravity.add(Gravity(400))
                    score.value -= 200




            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))
                # 防御壁：Sキー押下で発動
                if event.key == pg.K_s:
                    # スコア50以上＆既に壁がないときだけ発動
                    if score.value >= 50 and len(shields) == 0:
                        shields.add(Shield(bird, life=400))
                        score.value -= 50  # 消費スコア

        screen.blit(bg_img, [0, 0])

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())



        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        # Shieldと爆弾の衝突（ここではスコアは増やさない）
        hit_dict = pg.sprite.groupcollide(shields, bombs, False, True)
        for sh, hit_bombs in hit_dict.items():
            for bomb in hit_bombs:
                exps.add(Explosion(bomb, 50))

        
        for bomb in pg.sprite.groupcollide(bombs, gravity, True, False).keys():  # 力場と衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():  # 力場と衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for emy in pg.sprite.spritecollide(bird, emys, True):  # こうかとんと衝突した爆弾リスト
            if bird.state == "hyper":
                exps.add(Explosion(emy, 50))  # 爆発エフェクト
                score.value += 1  # 1点アップ
            
            else: #敵と衝突したら？
                bird.hp-=1 #HPが減る
                emy.kill()
                if bird.hp<=0:
                    #ゲームオーバー
                    bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                    score.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return

        gravity.update()
        gravity.draw(screen)
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update(bird.rect.center)
        emys.draw(screen)
        bombs.update()
        bombs.draw(screen)
        shields.update()
        shields.draw(screen)
        exps.update()
        exps.draw(screen)

        emps.update()
        emps.draw(screen)
        score.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()