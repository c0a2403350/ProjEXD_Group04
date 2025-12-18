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
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10
        self.state = "normal"
        self.hyper_life = 0

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
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/{i}.png") for i in range(1, 4)]

    def __init__(self):
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = random.randint(50, 300)  # 爆弾投下インターバル

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置_boundまで降下したら，_stateを停止状態に変更する
        引数 screen：画面Surface
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)


class Score:
    """
    打ち落とした爆弾，敵機の数をスコアとして表示するクラス
    爆弾：1点
    敵機：10点
    Levelは `int(self.value/10)` で算出し，残りはゲージで表示する
    """
    def __init__(self):
        self.font = pg.font.Font(None, 36)
        self.color = (255, 255, 255)
        self.shadow_color = (0, 0, 0)
        self.value = 10
        # テキスト位置
        self.text_posision = (20, 20)
        # ゲージ位置とサイズ
        self.exp_bar_position = (130, 20)
        self.exp_bar_size = (WIDTH-200, 24)
        

    def update(self, screen: pg.Surface):
        # レベルと進捗を計算
        level = int(self.value / 10)
        progress = self.value % 10  # 0..9 (10で次レベル)

        # レベル表示（影付き）
        text = f"Level: {level}"
        shadow_surface = self.font.render(text, True, self.shadow_color)
        text_surface = self.font.render(text, True, self.color)
        screen.blit(shadow_surface, (self.text_posision[0] + 2, self.text_posision[1] + 2))
        screen.blit(text_surface, self.text_posision)

        # ゲージ描画
        gx, gy = self.exp_bar_position
        gw, gh = self.exp_bar_size

        # ゲージ描写のSurfaceを作成(透明度設定)
        exp_Surface = pg.Surface((gw,gh),pg.SRCALPHA)
        # 背景
        # bg_rect = pg.Rect(gx, gy, gw, gh)
        pg.draw.rect(exp_Surface, (150, 150, 150,150), (0,0,gw,gh))
        # 進捗フィル
        fill_w = int((progress / 10) * gw)
        if fill_w > 0:
            pg.draw.rect(exp_Surface, (50, 200, 50, 200), (0,0,fill_w,gh))
        # 枠線
        pg.draw.rect(exp_Surface, (200, 200, 200, 200), (0, 0, gw, gh), 2)

        #alpha値の設定
        exp_Surface.set_alpha(240)
        screen.blit(exp_Surface,(gx,gy))

        # 進捗テキスト（例: 3/10）を右側に表示
        prog_text = f"{progress}/10"
        prog_surface = self.font.render(prog_text, True, self.color)
        screen.blit(prog_surface, (gx + gw + 10, gy - 2))

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
class starting:
    """
    ホーム画面の表示
    ・タイトル
    ・スタート
    ・やめる
    """
    def __init__(self):
        self.title = pg.font.Font("misaki_mincho.ttf", 150)
        self.font = pg.font.Font("misaki_mincho.ttf", 36)
        self.color = (255, 255, 255)
        img = pg.image.load("fig/2.png")
        img2 = pg.image.load("fig/serihu_pass_icon.png")
        self.chicken_image = pg.transform.rotozoom(img, 0, 1.0)
        self.chicken_image2 = pg.transform.rotozoom(img, 0, 1.0)
            # 左右反転してテキストの両脇に置く
        self.chicken_image3 = pg.transform.flip(self.chicken_image2, True, False)
        self.triangle=pg.transform.rotozoom(img2,30,0.06)




        # メニュー状態
        self.options = ["start", "quit"]
        self.selected = 0

    def update(self, screen: pg.Surface):
        title = "tut伝説"

        # 背景の半透明オーバーレイを描く
        overlay = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        title_surf = self.title.render(title, True, self.color)
        tx = WIDTH // 2 - title_surf.get_width() // 2
        ty = HEIGHT // 6
        screen.blit(title_surf, (tx, ty))

        # タイトルの両脇にチキン画像を表示（左は反転画像，右は通常画像）
        if self.chicken_image and self.chicken_image3:
            img_w = self.chicken_image.get_width()
            img_h = self.chicken_image.get_height()
            title_cy = ty + title_surf.get_height() // 2
            iy = title_cy - img_h // 2
            left_x = tx - img_w - 24
            right_x = tx + title_surf.get_width() + 24
            # 左に反転画像、右に通常画像
            screen.blit(self.chicken_image, (left_x, iy))
            screen.blit(self.chicken_image3, (right_x, iy))

        # メニュー（選択肢）を描画
        start_y = HEIGHT // 2
        for i, opt in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected else self.color
            opt_surf = self.font.render(opt, True, color)
            ox = WIDTH // 2 - opt_surf.get_width() // 2
            oy = start_y + i * (opt_surf.get_height() + 10)
            screen.blit(opt_surf, (ox, oy))
            # 選択中の項目に合わせて三角形を表示
            if i == self.selected and self.triangle:
                tri_w = self.triangle.get_width()
                tri_h = self.triangle.get_height()
                tx = ox - tri_w - 12
                ty = oy + (opt_surf.get_height() - tri_h) // 2
                screen.blit(self.triangle, (tx, ty))

# class Ending:
#     """
#     エンディング描画の設定
#     ・画面表示
#     ・テキスト表示
#     """
#     def __init__(self):
#         self.font=pg.font.Font("misaki_mincho.ttf",36)
#         self.text_bg_color=(255,255,255)
#         self.display_position=(60,HEIGHT-90)
#         self.display_size=(WIDTH-200,HEIGHT-30)
#         self.image=pg.image.transform.rotozoom("fig/serihu_pass_icon.png",180,0.1)
    
#     def update(self,screen:pg.Surface):
#         text=["よくもやってくれたな...","貴様のその行い万死に値する...","判決を言い渡す...","退学だ"]



def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    bg_img = pg.image.load(f"fig/back_ground.png")
    bg_img = pg.transform.scale(bg_img, (WIDTH, HEIGHT))
    # bg_img.set_alpha(10)##残像エフェクト今後の新機能で追加できそう
    
    score = Score()
    start_screen = starting()
    mode = "start"  # "start" or "play"

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

            # スタート画面用のイベント処理
            if mode == "start":
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_UP:
                        start_screen.selected = max(0, start_screen.selected - 1)
                    elif event.key == pg.K_DOWN:
                        start_screen.selected = min(len(start_screen.options) - 1, start_screen.selected + 1)
                    elif event.key == pg.K_RETURN or event.key == pg.K_SPACE:
                        if start_screen.selected == 0:
                            mode = "play"
                        else:
                            return 0
                continue

            # 以下はゲームプレイ中のイベント処理
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if key_lst[pg.K_LSHIFT]:
                    nb = NeoBeam(bird, 3)  # 第２引数がビームの本数
                    beams.add(nb.gen_beams())
                else:
                    beams.add(Beam(bird))
            if event.type == pg.KEYDOWN and event.key == pg.K_RSHIFT and score.value > 100:
                bird.state = "hyper"
                bird.hyper_life = 500
                score.value -= 100
            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                if score.value >= 20:
                    emps.add(EMP(emys, bombs, screen))
                    score.value -= 20
            if event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                if score.value >= 200:
                    gravity.add(Gravity(400))
                    score.value -= 200

            if event.type == pg.KEYDOWN:
                if event.key == pg.K_SPACE:
                    beams.add(Beam(bird))
                if event.key == pg.K_s:
                    if score.value >= 50 and len(shields) == 0:
                        shields.add(Shield(bird, life=400))
                        score.value -= 50  # 消費スコア

        screen.blit(bg_img, [0, 0])

        # スタート画面を表示している場合はゲーム処理をスキップ
        if mode == "start":
            start_screen.update(screen)
            pg.display.update()
            tmr += 1
            clock.tick(50)
            continue

        if tmr % 200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0:
                # 敵機が停止状態に入ったら，intervalに応じて爆弾投下
                bombs.add(Bomb(emy, bird))

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

        # # こうかとんと爆弾の衝突
        # for bomb in pg.sprite.spritecollide(bird, bombs, True):
        #     bird.change_img(8, screen)  # こうかとん悲しみエフェクト
        #     score.update(screen)
        #     pg.display.update()
        #     time.sleep(2)
        #     return
        for bomb in pg.sprite.groupcollide(bombs, gravity, True, False).keys():  # 力場と衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ

        for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():  # 力場と衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            score.value += 10  # 10点アップ
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.spritecollide(bird, bombs, True):  # こうかとんと衝突した爆弾リスト
            if bird.state == "hyper":
                exps.add(Explosion(bomb, 50))  # 爆発エフェクト
                score.value += 1  # 1点アップ
            else:
                if bomb.state == "inactive":
                    bomb.kill()
                    continue
                else:
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
        emys.update()
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