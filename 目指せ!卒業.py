import math
import os
import random
import sys
import time
import pygame as pg

WIDTH = 1100 # ゲームウィンドウの幅
HEIGHT = 650 # ゲームウィンドウの高さ
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
        self.speed = 3
        self.state = "normal"
        self.hyper_life = 0
        self.dmg_eff_time = 0 #ダメージエフェクトのフレーム管理用
        self.hp=10
        self.item1 = None#武器ランダム
        self.item2 = None
        self.item3 = None
        self.item4 = None
        self.item5 = None
        self.playerlv=1

        if os.path.exists("fig/damage.mp3"):
            self.dmg_sound = pg.mixer.Sound("fig/damage.mp3") #ダメージエフェクト(elseはエラー回避用)
        else:
            self.dmg_sound = None


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


        self.speed = 3

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

        #ダメージエフェクト追加
        if self.dmg_eff_time > 0:
            self.dmg_eff_time -= 1
            self.image = self.image.copy()
            self.image.fill((255, 0, 0, 255), special_flags=pg.BLEND_RGBA_MULT)

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
        self.rect.centerx = bird.rect.centerx+bird.rect.height*self.vx
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
    def __init__(self, obj: "Bomb|Enemy|Bomb_Weapon", life: int, clr_change=False):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif").convert_alpha()
        if clr_change: #色変更
            img.fill((255, 0, 255), special_flags=pg.BLEND_RGB_MULT)

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
class Hpbar:
    """
    HPバーとレベルを表示する
    """
    def __init__(self,bird:Bird):
        self.bird = bird
        self.max_hp = bird.hp 
        self.width = 200
        self.height = 20
        self.image = pg.Surface((self.width, self.height))
        self.rect = self.image.get_rect()
        self.rect.center = 110, HEIGHT - 40
        self.font = pg.font.SysFont("meiryo", 20, bold=True)
    def update(self, screen: pg.Surface):
        self.image.fill((255, 0, 0))
        if self.bird.hp < 0:
            current_hp = 0
        else:
            current_hp = self.bird.hp
        ratio = current_hp / self.max_hp  # 現在HPの割合
        green_width = int(self.width * ratio)  
        pg.draw.rect(self.image, (0, 255, 0), (0, 0, green_width, self.height)) #HP緑部分
        pg.draw.rect(self.image, (255, 255, 255), (0, 0, self.width, self.height), 2) #枠
        screen.blit(self.image, self.rect) #ダメージ食らった割合
        bird_txt = f"こうかとん  Level:{self.bird.playerlv}"
        bird_txt_img = self.font.render(bird_txt, True, (255, 255, 255))
        txt_rect = bird_txt_img.get_rect()
        txt_rect.centerx = self.rect.centerx
        txt_rect.bottom = self.rect.top - 5
        screen.blit(bird_txt_img, txt_rect)
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
        WIDTH = 20
        height = bird.rect.height * 2

        # 手順1：空のSurfaceを生成（アルファ付き）
        base_image = pg.Surface((WIDTH, HEIGHT), pg.SRCALPHA)

        # 手順2：青いrectを描画
        pg.draw.rect(base_image, (0, 0, 255), (0, 0, WIDTH, HEIGHT))

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


"""
武器に関するクラス
"""
class Bomb_Weapon(pg.sprite.Sprite):
    """
    ボム武器に関するクラス
    爆弾を設置する。これ自体に攻撃性は持たせない
    """
    def __init__(self, bird: "Bird"):
        """
        初期化処理
        引数：Birdインスタンス
        """
        super().__init__()
        
        #画像設定
        self.image = pg.image.load("fig/bomb.png")
        self.image = pg.transform.scale(self.image, (100, 100))
        #Rect取得
        self.rect = self.image.get_rect()
        self.rect.center = bird.rect.center

        #ステータス設定
        self.lv = 1 #レベル
        self.atk = 5 #攻撃力
        self.cnt = 100 #表示時間
    
    def update(self, screen: pg.Surface):
        """
        描画処理
        引数；表示用Surface
        カウンタが0になるまで表示する
        """
        self.cnt -= 1
        screen.blit(self.image, self.rect) #自己描画
        
        #カウンタが0になったら削除
        if self.cnt == 0:
            self.kill()

class Laser_Weapon(pg.sprite.Sprite):
    """
    レーザー武器に関するクラス
    レーザーを発射する
    """
    def __init__(self, bird: "Bird"):
        """
        初期化処理
        引数：Birdインスタンス
        """
        super().__init__()
        
        #角度設定
        self.vx, self.vy = bird.dire #鳥の角度を取得
        angle = math.degrees(math.atan2(-self.vy, self.vx)) #レーザーの角度の設定

        #画像設定
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/laser.png"), angle, 1.0)
        self.image = pg.transform.scale(self.image, (200, 200))

        #移動設定
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))

        self.rect = self.image.get_rect() #Rect取得
        #中央座標の設置
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx

        #ステータス設定
        self.lv = 1 #レベル
        self.atk = 1 #攻撃力
        self.speed = 10 #レーザーの速さ
    
    def update(self):
        """
        描画処理
        画面外に行ったらオブジェクト削除
        """
        #移動
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy) #移動処理

        #画面外への移動で削除
        if check_bound(self.rect) != (True, True):
            self.kill()

class Missile_Weapon(pg.sprite.Sprite):
    """
    追尾ミサイル武器に関するクラス
    一番近い敵をターゲットに追尾し続ける
    """
    def __init__(self, bird: "Bird", emys: pg.sprite.Group):
        """
        初期化処理
        引数：Birdインスタンス, Enemyオブジェクトを格納するsprite.Group
        """
        super().__init__()
        
        #ターゲット設定
        self.target = None
        min_dist = float("inf") #最小を格納する変数(初期値：無限)
        #鳥との距離が一番小さい敵をターゲットにする
        for emy in emys:
            dx = emy.rect.centerx - bird.rect.centerx #距離との差x
            dy = emy.rect.centery - bird.rect.centery #距離との差y
            
            dist = math.sqrt(dx**2 + dy**2) #鳥と敵の直線距離
            
            #最小の上書き
            if dist < min_dist:
                min_dist = dist
                self.target = emy
        #敵がいなければこのオブジェクトを削除
        if self.target is None:
            self.kill()
            return
        else:
            #敵から鳥の中心までのx, y成分
            self.vx = self.target.rect.centerx - bird.rect.centerx
            self.vy = self.target.rect.centery - bird.rect.centery

        #画像設定
        self.base_image = pg.image.load("fig/missile.png")
        self.base_image = pg.transform.scale(self.base_image, (100, 50))
        
        self.image = self.base_image
        self.rect = self.image.get_rect() #Rect取得
        self.rect.center = bird.rect.center #Rectの中央を鳥のRectの中央に合わせる

        #ステータス設定
        self.lv = 1 #レベル
        self.atk = 10 #攻撃力
        self.spd = 20 #速度        
    
    def update(self):
        """
        描画処理
        ターゲットにぶつかるまで、常にターゲットした敵の方向に向いて移動する。
        """
        #ターゲットが消失したなら削除
        if not (self.target and self.target.alive()):
            self.kill()
            return
        
        #敵の中心とミサイル中心のx,y成分
        dx = self.target.rect.centerx - self.rect.centerx
        dy = self.target.rect.centery - self.rect.centery
        #直線距離の算出
        norm = math.sqrt(dx*dx + dy*dy)
        if norm == 0:
            return
        
        #正規化処理(vx + vy = 1)
        self.vx = dx / norm
        self.vy = dy / norm

         #逆正接の算出
        angle = math.degrees(math.atan2(-self.vy, self.vx))

        center = self.rect.center #中央の保持
        #画像の角度変更
        self.image = pg.transform.rotozoom(self.base_image, angle, 1.0)
        self.rect = self.image.get_rect(center=center)

        #移動
        self.rect.move_ip(self.spd * self.vx, self.spd * self.vy)

class Gun_Weapon(pg.sprite.Sprite):
    """
    連続弾武器に関するクラス
    連続的に弾を射出する
    """
    def __init__(self, bird: "Bird", space: int):
        """
        初期化処理
        引数：Birdインスタンス, 鳥中心からのずらし整数量
        """
        super().__init__()

        #角度設定
        self.vx, self.vy = bird.dire #鳥の角度取得
        angle = math.degrees(math.atan2(-self.vy, self.vx)) #弾の角度設定

        #画像設定
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/bullet.png"), angle, 1.0)
        self.image = pg.transform.scale(self.image, (20, 20))

        #移動設定
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))

        self.rect = self.image.get_rect() #Rect取得
        #中心座標の設定
        self.rect.centery = bird.rect.centery + bird.rect.height * self.vy + space
        self.rect.centerx = bird.rect.centerx + bird.rect.width * self.vx + space

        #ステータス設定
        self.lv = 1 #レベル
        self.atk = 1 #攻撃力
        self.speed = 10 #弾速
    
    def update(self):
        """
        描画処理
        画面外に行ったらオブジェクト削除
        """
        #移動
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)

        #画面外への移動で削除
        if check_bound(self.rect) != (True, True):
            self.kill()
            
class Sword_Wepon(pg.sprite.Sprite):
    """
    円の軌道で周回する武器に関するクラス
    """
    def __init__(self, bird: "Bird"):
        """
        初期化処理
        引数：Birdインスタンス
        """
        super().__init__()
        
        self.bird = bird
        self.angle = 0.0 #初期化角度
        
        #画像設定
        self.base_image = pg.image.load("fig/sword.png")
        self.base_image = pg.transform.scale(self.base_image, (100, 100))
        
        self.image = self.base_image
        self.rect = self.image.get_rect() #Rect取得
        
        #ステータス設定
        self.lv = 1 #レベル
        self.atk = 5 #攻撃力
        self.radius = 100 #周回半径
        self.spd = 0.07 #周回速度
        
    def update(self):
        """
        描画処理
        円の軌道でbirdのまわりを周回する
        """
        self.angle += self.spd #角度の変化
        cx, cy  = self.bird.rect.center #鳥の中心を取得
        
        #中心座標の決定
        x = cx + self.radius * math.cos(self.angle)
        y = cy + self.radius * math.sin(self.angle)
        center = (x, y)
        
        #画像角度の決定
        dx = x - cx
        dy = y - cy
        image_angle = -math.degrees(math.atan2(dy, dx))

        #画像角度の変更
        self.image = pg.transform.rotate(self.base_image, image_angle)
        self.rect = self.image.get_rect(center=center)          
        
def main():
    global width, height
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    width, height = screen.get_width(), screen.get_height()
    bg_img = pg.image.load(f"fig/back_ground.png")
    bg_img = pg.transform.scale(bg_img, (WIDTH, HEIGHT))

    #武器権限時の効果音
    bb_se = pg.mixer.Sound("sound/bb.wav")
    bb_se.set_volume(0.4)
    exp_se = pg.mixer.Sound("sound/bb_effct.wav")
    exp_se.set_volume(0.2)
    gun_se = pg.mixer.Sound("sound/gun.wav")
    gun_se.set_volume(0.1)    
    laser_se = pg.mixer.Sound("sound/laser.wav")
    laser_se.set_volume(0.1)
    mssl_se = pg.mixer.Sound("sound/mssle.wav")
    mssl_se.set_volume(0.4)
    swrd_se = pg.mixer.Sound("sound/sword.wav")
    swrd_se.set_volume(1)    

    # bg_img.set_alpha(10)##残像エフェクト今後の新機能で追加できそう
    
    score = Score()
    start_screen = starting()
    mode = "start"  # "start" or "play"

    bird = Bird(3, (900, 400))
    hpbar = Hpbar(bird)

    
    bb_wep = pg.sprite.Group() #ボムの武器のグループ
    bb_effect = pg.sprite.Group() #ボム演出後の攻撃用エフェクトグループ
    lsr_wep = pg.sprite.Group() #レーザー武器のグループ
    mssl_wep = pg.sprite.Group() #ミサイル武器のグループ
    gun_wep = pg.sprite.Group() #連続弾武器のグループ
    swrd_wep = pg.sprite.Group() #周回軌道武器のグループ
    bombs = pg.sprite.Group()
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    gravity = pg.sprite.Group()
    emys = pg.sprite.Group()
    shields = pg.sprite.Group()  # 防御壁グループ（1つだけ存在）
    emps = pg.sprite.Group()

    tmr = 0
    laser_power = 100 #レーザー射出管理用カウンタ
    sword_recast = 500 #剣の持続カウンタ

    swrd_wep.add(Sword_Wepon(bird)) #剣武器追加
    swrd_se.play(-1)
    

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

        if tmr % 20 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())
            
        #武器処理
        #爆弾クールダウン
        if tmr % 150 == 0 and tmr != 0:
            bb_wep.add(Bomb_Weapon(bird)) #演出用ボムを追加
            bb_se.play()
        for bb in bb_wep:
            if bb.cnt == 1:
                bb_effect.add(Explosion(bb, 100, True)) #攻撃判定エフェクトの追加

                exp_se.play()

        #レーザークールダウン
        if tmr % 9 == 0:
            laser_power -= 1
            
            if laser_power > 80: #射出上限
                lsr_wep.add(Laser_Weapon(bird)) #レーザー武器追加
                laser_se.play()
            elif laser_power == 0:
                laser_power = 100 #初期化
                
        #ミサイルクールダウン
        if tmr % 100 == 0:
            mssl_wep.add(Missile_Weapon(bird, emys)) #ミサイル武器追加
            mssl_se.play()

        #連続弾クールダウン
        if tmr % 5 == 0:
            #連続弾追加
            gun_wep.add(Gun_Weapon(bird, 10))
            gun_wep.add(Gun_Weapon(bird, -10))

            gun_se.play()

        #剣クールダウン
        sword_recast -= 1
        if sword_recast == 0:
            swrd_wep.empty() #すべての周回軌道武器を削除

            swrd_se.stop()
        elif sword_recast == -500: #クールタイム
            #初期化
            sword_recast = 500
            swrd_wep.add(Sword_Wepon(bird)) #周回軌道武器の追加
            swrd_se.play(-1)

        #ボム衝突イベント
        #敵との衝突
        for emy, bb_mine in pg.sprite.groupcollide(emys, bb_wep, False, True).items():
            for bb in bb_mine:
                bb_effect.add(Explosion(bb, 100, True)) #即座に起爆

                exp_se.play()
        #敵攻撃との衝突
        for bb_emy, bb_mine in pg.sprite.groupcollide(bombs, bb_wep, True, True).items():
            for bb in bb_mine:
                bb_effect.add(Explosion(bb, 100, True)) #即座に起爆

                exp_se.play()
        
        #敵×武器衝突イベント
        #ボム攻撃用エフェクトとの衝突
        for emy in pg.sprite.groupcollide(emys, bb_effect, True, False).keys():
            exps.add(Explosion(emy, 100))
            score.value += 1
        #レーザー武器との衝突
        for emy in pg.sprite.groupcollide(emys, lsr_wep, True, False).keys():
            exps.add(Explosion(emy, 100))
            score.value += 1
        #追尾ミサイルとの衝突
        for emy in pg.sprite.groupcollide(emys, mssl_wep, True, True).keys():
            exps.add(Explosion(emy, 100))
            score.value += 1
        #連続弾との衝突
        for emy in pg.sprite.groupcollide(emys, gun_wep, True, True).keys():
            exps.add(Explosion(emy, 100))
            score.value += 1
        #周回軌道武器との衝突
        for emy in pg.sprite.groupcollide(emys, swrd_wep, True, False).keys():
            exps.add(Explosion(emy, 100))
            score.value += 1

        #敵攻撃×武器衝突イベント
        #ボム攻撃用エフェクトとの衝突
        for bb in pg.sprite.groupcollide(bombs, bb_effect, True, False).keys():
            exps.add(Explosion(bb, 100))
        #レーザー武器との衝突
        for bb in pg.sprite.groupcollide(bombs, lsr_wep, True, False).keys():
            exps.add(Explosion(bb, 100))
        #追尾ミサイルとの衝突
        for bb in pg.sprite.groupcollide(bombs, mssl_wep, True, True).keys():
            exps.add(Explosion(bb, 100))
        #連続弾との衝突
        for bb in pg.sprite.groupcollide(bombs, gun_wep, True, True).keys():
            exps.add(Explosion(bb, 100))
        #周回軌道武器との衝突
        for bb in pg.sprite.groupcollide(bombs, swrd_wep, True, False).keys():
            exps.add(Explosion(bb, 100))
                                



        for emy in pg.sprite.groupcollide(emys, beams, True, True).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for bomb in pg.sprite.groupcollide(bombs, beams, True, True).keys():  # ビームと衝突した爆弾リスト
            exps.add(Explosion(bomb, 50))  # 爆発エフェクト
            score.value += 1  # 1点アップ
            
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
            
        for emy in pg.sprite.groupcollide(emys, gravity, True, False).keys():  # 力場と衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            
            bird.change_img(6, screen)  # こうかとん喜びエフェクト

        for emy in pg.sprite.spritecollide(bird, emys, True):  # こうかとんと衝突した爆弾リスト
            if bird.state == "hyper":
                exps.add(Explosion(emy, 50))  # 爆発エフェクト
                
            else: #敵と衝突したら？
                bird.hp-=1 #HPが減る
                emy.kill()
                bird.dmg_eff_time = 50
                if bird.dmg_eff_time and bird.dmg_sound is not None:
                    bird.dmg_sound.play()
                
                if bird.hp<=0:
                    #ゲームオーバー
                    bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                    hpbar.update(screen)
                    pg.display.update()
                    time.sleep(2)
                    return

        score.update(screen)
        gravity.update()
        gravity.draw(screen)
        bird.update(key_lst, screen)        
        bb_wep.update(screen)
        bb_effect.update()
        bb_effect.draw(screen)
        lsr_wep.update()
        lsr_wep.draw(screen)
        mssl_wep.update()
        mssl_wep.draw(screen)
        gun_wep.update()
        gun_wep.draw(screen)
        swrd_wep.update()
        swrd_wep.draw(screen)
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
        hpbar.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    pg.mixer.init()
    main()
    pg.quit()
    sys.exit()