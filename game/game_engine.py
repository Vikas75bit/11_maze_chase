import pygame
from game.maze import generate_maze, CELL
from game.entities import Player, Enemy

COLS, ROWS = 13, 11
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 50
FPS = 60

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Chase")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.hud_font = pygame.font.SysFont("monospace", 16)
        self.big_font = pygame.font.SysFont("monospace", 38, bold=True)
        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.player = Player(0, 0)
        self.score = 0
        self.enemies = [
            Enemy(ROWS-1, COLS-1),
            Enemy(0, COLS-1),
            Enemy(ROWS-1, 0),
        ]
        self.game_start_ticks = pygame.time.get_ticks()
        self.speed_tier = 0
        self.base_move_interval = self.enemies[0].move_interval
        pellet_center = ((COLS // 2 + 2) * CELL + CELL // 2,
                         (ROWS // 2) * CELL + CELL // 2)
        self.power_pellet_rect = pygame.Rect(0, 0, 18, 18)
        self.power_pellet_rect.center = pellet_center
        self.power_pellet_collected = False
        self.freeze_frames_remaining = 0
        self.exit_rect = pygame.Rect((COLS//2)*CELL+5, (ROWS//2)*CELL+5, CELL-10, CELL-10)
        self.caught = False
        self.won = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r: self.reset()
        return True

    def update(self):
        if self.caught or self.won: return
        self.score += 1
        elapsed_seconds = (pygame.time.get_ticks() - self.game_start_ticks) // 1000
        max_speed_tier = max(0, (self.base_move_interval - 5 + 1) // 2)
        self.speed_tier = min(elapsed_seconds // 15, max_speed_tier)
        move_interval = max(5, self.base_move_interval - 2 * self.speed_tier)
        for enemy in self.enemies:
            enemy.move_interval = move_interval
        if self.freeze_frames_remaining == 0:
            for enemy in self.enemies:
                enemy.frozen = False
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, ROWS, COLS)
        if (not self.power_pellet_collected
                and self.player.rect.colliderect(self.power_pellet_rect)):
            self.power_pellet_collected = True
            self.freeze_frames_remaining = 300
            for enemy in self.enemies:
                enemy.frozen = True
        enemies_frozen = self.freeze_frames_remaining > 0
        for enemy in self.enemies:
            if not enemies_frozen:
                enemy.update(self.walls, self.player, ROWS, COLS)
            if self.player.rect.colliderect(enemy.rect):
                self.caught = True
        if enemies_frozen:
            self.freeze_frames_remaining -= 1
        if self.player.rect.colliderect(self.exit_rect):
            self.won = True

    def draw(self):
        self.screen.fill((230, 220, 210))
        wc=(50,40,60)
        for r in range(ROWS):
            for c in range(COLS):
                x,y=c*CELL,r*CELL
                w=self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen,wc,(x,y),(x+CELL,y),3)
                if w[1]: pygame.draw.line(self.screen,wc,(x,y+CELL),(x+CELL,y+CELL),3)
                if w[2]: pygame.draw.line(self.screen,wc,(x+CELL,y),(x+CELL,y+CELL),3)
                if w[3]: pygame.draw.line(self.screen,wc,(x,y),(x,y+CELL),3)
        pygame.draw.rect(self.screen,(80,200,80),self.exit_rect,border_radius=4)
        lbl=self.font.render("EXIT",True,(20,80,20))
        self.screen.blit(lbl,(self.exit_rect.x+2,self.exit_rect.y+6))
        if not self.power_pellet_collected:
            pygame.draw.circle(self.screen,(255,220,40),self.power_pellet_rect.center,9)
            pygame.draw.circle(self.screen,(255,250,180),self.power_pellet_rect.center,9,2)
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
            if enemy.frozen:
                frozen_lbl = self.hud_font.render("FROZEN",True,(40,190,255))
                self.screen.blit(frozen_lbl,(enemy.rect.centerx-frozen_lbl.get_width()//2,
                                             enemy.rect.y-frozen_lbl.get_height()-4))
        hud=pygame.Rect(0,ROWS*CELL,WIDTH,50)
        pygame.draw.rect(self.screen,(30,30,50),hud)
        info=self.hud_font.render("Reach EXIT before the enemy catches you!  R=Restart",True,(200,200,200))
        self.screen.blit(info,(8,ROWS*CELL))
        tier=self.hud_font.render(f"Speed Tier: {self.speed_tier}",True,(200,200,200))
        self.screen.blit(tier,(8,ROWS*CELL+25))
        survived=self.hud_font.render(f"Survived: {self.score // 60}s",True,(200,200,200))
        self.screen.blit(survived,(WIDTH-survived.get_width()-8,ROWS*CELL+25))
        if self.caught:
            self._overlay("CAUGHT!", (220,60,60))
        if self.won:
            self._overlay("ESCAPED!", (80,220,80))
        pygame.display.flip()

    def _overlay(self, text, color):
        surf=pygame.Surface((WIDTH,ROWS*CELL),pygame.SRCALPHA)
        surf.fill((0,0,0,140))
        self.screen.blit(surf,(0,0))
        msg=self.big_font.render(text,True,color)
        survived=self.font.render(f"Survived: {self.score // 60}s",True,(255,255,255))
        sub=self.font.render("Press R to Restart",True,(200,200,200))
        self.screen.blit(msg,(WIDTH//2-msg.get_width()//2,ROWS*CELL//2-55))
        self.screen.blit(survived,(WIDTH//2-survived.get_width()//2,ROWS*CELL//2+5))
        self.screen.blit(sub,(WIDTH//2-sub.get_width()//2,ROWS*CELL//2+40))

    def run(self):
        running=True
        while running:
            running=self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
