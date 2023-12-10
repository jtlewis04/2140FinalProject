import arcade
import pathlib
import math
import explosion as ex
import time
import random
# Constants
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 750
PLAYER_RADIUS = 50
MAP_SCALING = 1.0

ASSETS_PATH = str(pathlib.Path(__file__).resolve().parent) + '/assets'

class Player(arcade.Sprite):
    def __init__(self, center_x):
        super().__init__(ASSETS_PATH+'/fighter.png')  # Replace with your player sprite file
        self.center_x = center_x
        self.center_y = 25
        

class Enemy(arcade.Sprite):
    def __init__(self,spawn_x, spawn_y):
        super().__init__(ASSETS_PATH+'/enemy.png')  # Replace with your player sprite file
        self.center_x = spawn_x
        self.center_y = spawn_y
        self.change_y = -2
    
    

class Missile(arcade.Sprite):
    def __init__(self,spawn_x, spawn_y):
        super().__init__(ASSETS_PATH+'/missile.png')  # Replace with your player sprite file
        self.center_x = spawn_x
        self.center_y = spawn_y
        self.change_y = 5
        
    
    def update(self):
        if self.center_y > SCREEN_HEIGHT:
            self.kill()
        else:
            return super().update()

class HumanVsAiView(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.BLACK)

        # Scene with all sprites
        self.scene = None
        # Player sprite
        self.player = None
        # Time at which a missile was last shot
        self.last_shot = time.time()
        # Time at which last missile was fired by AI player
        self.last_shot_ai = time.time()
        # Wave number, larger numbers are more difficult
        self.wave = 0
        # Tied to wave difficulty
        self.enemies_per_y = 1
        # Is the game over?
        self.game_over = 0
        # How long since player blew up, allows for explosion to finish before quitting
        self.time_since_game_over = 0
        self.setup()

    def setup(self):
        # Get file path to TileMap
        map_path = ASSETS_PATH + '/galaga_map.tmx'

        # Specify layer options
        layer_options = {
            'game_borders': {
                'use_spatial_hash': True,
            },
        }
        #Load map
        self.tile_map = arcade.tilemap.TileMap(map_path, MAP_SCALING,layer_options,None,'Simple',4.5,None,(0,375))
        
        # Initialize scene using map
        self.scene = arcade.Scene.from_tilemap(self.tile_map)
        # Add second game screen for AI player
        self.ai_background = arcade.sprite.Sprite(ASSETS_PATH + '/background.png',center_x=850,center_y=375,image_height=750,image_width=500)
        self.scene.add_sprite('ai_background',self.ai_background)
        # Initialize score
        self.score = 0
        # Initialize player
        self.player = Player(250)
        self.scene.add_sprite('player',self.player)
        # Initialize AI player
        self.ai_player = Player(850)
        self.scene.add_sprite('cpu',self.ai_player)
        

        # Add empty lists for enemies, missiles, and explosions
        self.scene.add_sprite_list('enemies')
        self.scene.add_sprite_list('missiles')
        self.scene.add_sprite_list('explosions')

        
    def on_draw(self):
        arcade.start_render()
        # Clear the screen
        self.clear()

        # Draw the scene
        self.scene.draw()

        #Render the Score text
        arcade.draw_text(f"Score: {self.score}", 10, SCREEN_HEIGHT - 25, arcade.color.WHITE, 20)
        #Render the Wave text
        arcade.draw_text(f"Wave: {self.wave}", 380, SCREEN_HEIGHT - 25, arcade.color.WHITE, 20)


    def on_update(self, delta_time):
        # Check for game_over state
        if not self.game_over or self.time_since_game_over + 2 > time.time():
            # Ensure player stays within game bounds
            if ((self.player.center_x > 25 or self.player.change_x != -5) and \
                (self.player.center_x < 475 or self.player.change_x != 5)):
                self.player.update()
            else:
                self.player.change_x = 0
            
            enemies = self.scene.get_sprite_list('enemies')
            missiles = self.scene.get_sprite_list('missiles')

            # ********************************** AI PLAYER **************************************
            # Type of 'AI' depends on wave number, every 3rd wave a new algorithm takes over
            if self.wave < 3:
                # First algorithm is a CPU controlled by a random number generator
                if self.last_shot_ai + 0.25 < time.time():
                    self.ai_player.center_x = random.randint(0,9) * 50 + 625
                    missiles.append(Missile(self.ai_player.center_x,self.ai_player.center_y+50))
                    self.last_shot_ai = time.time()


            # No enemies means the wave has been beaten, so move onto next wave and spawn the enemies
            if len(enemies) == 0:
                self.wave += 1
                # Ramp the difficulty by increasing enemies per why every 3 waves
                if self.wave % 3 == 0:
                    self.enemies_per_y  += 1
                # Spawn 6 + (2 * wave# % 3) * enemies_per_y enemies per wave
                for y in range(6+ 2*(self.wave%3)):
                    for x in range(self.enemies_per_y):
                        # Split the screen width depending on the enemies per y, spawning one enemy in each section
                        spawn_x = random.randrange(10*x//self.enemies_per_y, 10*(x+1)//self.enemies_per_y) * 50 + 25
                        spawn_x_ai = spawn_x+600
                        # every 200 pixels is a new y level
                        enemies.extend([Enemy(spawn_x,SCREEN_HEIGHT+200*y),Enemy(spawn_x_ai,SCREEN_HEIGHT+200*y)])
                        

            # If enemy and missile are colliding, destroy them both, create explosion
            # then check if any enemies have reached the player to end the game
            for enemy in enemies:
                for missile in missiles:
                    if enemy.collides_with_sprite(missile):
                        enemy.kill()
                        missile.kill()
                        # Increase score
                        self.score += 10
                        # Make an explosion
                        for i in range(ex.PARTICLE_COUNT):
                            explosions_list = self.scene.get_sprite_list('explosions')
                            particle = ex.Particle(explosions_list)
                            particle.position = enemy.position
                            explosions_list.append(particle)

                        smoke = ex.Smoke(50)
                        smoke.position = enemy.position
                        explosions_list.append(smoke)
                        continue
                # If enemy has reached player's y level, end the game
                if enemy.center_y <= 50 and not self.game_over:
                    player = self.player
                    self.game_over = 1
                    if enemy.center_x > 500:
                        player = self.ai_player
                        self.game_over = 2
                    self.time_since_game_over = time.time()
                    # Make an explosion on player who died
                    # Make an explosion on enemy
                    for i in range(ex.PARTICLE_COUNT):
                        explosions_list = self.scene.get_sprite_list('explosions')
                        particle_e = ex.Particle(explosions_list)
                        particle_e.position = enemy.position
                        particle_p = ex.Particle(explosions_list)
                        particle_p.position = player.position
                        explosions_list.append(particle_e)
                        explosions_list.append(particle_p)
                    smoke_e = ex.Smoke(50)
                    smoke_p = ex.Smoke(50)
                    smoke_e.position = enemy.position
                    smoke_p.position = player.position
                    explosions_list.append(smoke_e)
                    explosions_list.append(smoke_p)
                    enemy.kill()
                    player.kill()

            # Missiles and enemies update regardless of player movement
            self.scene.update(['enemies','missiles','explosions'])
        else:
            game_over_view = GameOverView(self.score,self.wave, self.game_over)
            self.window.set_size(480,710)
            self.window.show_view(game_over_view)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.LEFT:
            self.player.change_x = -5
        elif key == arcade.key.RIGHT:
            self.player.change_x = 5
        elif key == arcade.key.SPACE:
            # Ensure a 0.5 second delay between missile firing
            if self.last_shot <= time.time() - 0.5:
                self.scene.get_sprite_list('missiles').append(Missile(self.player.center_x,self.player.center_y+50))
                self.last_shot = time.time()
        elif key == arcade.key.ESCAPE:
            title_view = TitleView(self)
            self.window.set_size(480,710)
            self.window.show_view(title_view)
            

    def on_key_release(self, key, modifiers):
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player.change_x = 0

# Title screen
class TitleView(arcade.View):
    def __init__(self, paused_game = None) -> None:
        super().__init__()
        #Load title image
        self.title_image = arcade.load_texture(ASSETS_PATH+'/title_screen.png')

        # Set our display timer
        self.display_timer = 1.0

        # Is the start text visible?
        self.show_start = False

        # Are the instructions being shown?
        self.showing_instructions = False

        # Store paused game (or nothing if running for first time)
        self.paused_game = paused_game
    
    
    def on_update(self, delta_time: float) -> None:
        # First, count down the time
        self.display_timer -= delta_time

        # If the timer has run out, toggle start text
        if not self.showing_instructions:
            if self.display_timer < 0:
                self.show_start = not self.show_start
                # And reset the timer so the start text flashes slowly
                self.display_timer = 2
        else:
            self.show_start = False

            
    def on_draw(self) -> None:
        # Start the rendering loop
        arcade.start_render()

        # Draw a rectangle filled with our title image
        arcade.draw_texture_rectangle(
            center_x=SCREEN_WIDTH / 2,
            center_y=SCREEN_HEIGHT / 2,
            width=SCREEN_WIDTH,
            height=SCREEN_HEIGHT,
            texture=self.title_image,
        )

        # Show instructions if I is pressed
        if self.showing_instructions:
            arcade.draw_text(
                "Movement:",
                start_x=30,
                start_y=300,
                color=arcade.color.FLORAL_WHITE,
                font_size=20
            )
            arcade.draw_text(
                "   - Arrows to move", start_x=30, start_y=270, color=arcade.color.FLORAL_WHITE, font_size=20
            )
            arcade.draw_text(
                "   - SPACE to shoot", start_x=30, start_y=240, color=arcade.color.FLORAL_WHITE, font_size=20
            )
            arcade.draw_text(
                "Gain score for each enemy destroyed", start_x=30, start_y=210, color=arcade.color.FLORAL_WHITE, font_size=20
            )
            arcade.draw_text(
                "ESC to pause and quit to title", start_x=30, start_y=180, color=arcade.color.FLORAL_WHITE, font_size=20
            )
            arcade.draw_text(
                "           Press ESC to return", start_x=30, start_y=150, color=arcade.color.RED, font_size=20
            )
            
        # Show start if not blinking out
        if self.show_start:
            if self.paused_game == None:
                arcade.draw_text(
                    "Space to Start | I for Instructions",
                    start_x=30,
                    start_y=210,
                    color=arcade.color.FLORAL_WHITE,
                    font_size=22,
                )
            else:
                arcade.draw_text(
                    "Space to Resume | I for Instructions",
                    start_x=30,
                    start_y=210,
                    color=arcade.color.FLORAL_WHITE,
                    font_size=20,
                )
                arcade.draw_text(
                    "             R to Restart Game",
                    start_x=30,
                    start_y=170,
                    color=arcade.color.FLORAL_WHITE,
                    font_size=20,
                )

        
    def on_key_press(self, key: int, modifiers: int) -> None:
        if self.paused_game == None:
            if key == arcade.key.SPACE:
                if not self.showing_instructions:
                    game_view = HumanVsAiView()
                    game_view.setup()
                    self.window.set_size(1080,710)
                    self.window.show_view(game_view)
            elif key == arcade.key.I:
                self.showing_instructions = True
            elif key == arcade.key.ESCAPE:
                self.showing_instructions = False
        else:
            if key == arcade.key.SPACE:
                if not self.showing_instructions:
                    self.window.set_size(1080,710)
                    self.window.show_view(self.paused_game)
            elif key == arcade.key.I:
                self.showing_instructions = True
            elif key == arcade.key.ESCAPE:
                self.showing_instructions = False
            elif key == arcade.key.R:
                game_view = HumanVsAiView()
                game_view.setup()
                self.window.set_size(1080,710)
                self.window.show_view(game_view)

class GameOverView(arcade.View):
    def __init__(self, score, wave, game_over) -> None:
        super().__init__()
        #Load title image
        self.title_image = arcade.load_texture(ASSETS_PATH+'/title_screen.png')
        # Set our display timer
        self.display_timer = 1.0
        # Who lost the game? (1=Player,2=AI)
        self.game_over = game_over
        # Is the text visible?
        self.show_text = False
        # Game end score
        self.score = score
        # Game end wave
        self.wave = wave

    def on_update(self, delta_time: float) -> None:
        # First, count down the time
        self.display_timer -= delta_time

        # If the timer has run out, toggle text
        if self.display_timer < 0:
            self.show_text = not self.show_text
            # And reset the timer so the text flashes slowly
            self.display_timer = 2

    def on_draw(self) -> None:
        # Start the rendering loop
        arcade.start_render()

        # Draw a rectangle filled with our title image
        arcade.draw_texture_rectangle(
            center_x=SCREEN_WIDTH / 2,
            center_y=SCREEN_HEIGHT / 2,
            width=SCREEN_WIDTH,
            height=SCREEN_HEIGHT,
            texture=self.title_image,
        )
        if self.game_over == 2:
            arcade.draw_text(
                        f"     You Beat The AI!",
                        start_x=30,
                        start_y=335,
                        color=arcade.color.MINT_GREEN,
                        font_size=30,
                    )
        else:
            arcade.draw_text(
                        f"         The AI Wins...",
                        start_x=30,
                        start_y=335,
                        color=arcade.color.RED_DEVIL,
                        font_size=30,
                    )
        arcade.draw_text(
                    f"                  Score: {self.score}",
                    start_x=30,
                    start_y=250,
                    color=arcade.color.FLORAL_WHITE,
                    font_size=22,
                )
        arcade.draw_text(
                    f"                  Wave: {self.wave}",
                    start_x=30,
                    start_y=290,
                    color=arcade.color.FLORAL_WHITE,
                    font_size=22,
                )
        
        # Show text if not blinking out
        if self.show_text:
            arcade.draw_text(
                "     ESCAPE to Return to Title",
                start_x=30,
                start_y=210,
                color=arcade.color.FLORAL_WHITE,
                font_size=22,
            )
        
    def on_key_press(self, key: int, modifiers: int) -> None:
        if key == arcade.key.ESCAPE:
            title_view = TitleView()
            self.window.show_view(title_view)
            

def main():
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "HumanVsAi")
    title_view = TitleView()
    window.set_size(480,710)
    window.show_view(title_view)
    arcade.run()

if __name__ == "__main__":
    main()
