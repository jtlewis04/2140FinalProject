import time
import random
import subprocess
import sys
# Try and install arcade if user hasn't already
try:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'arcade'])
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pathlib'])   
    print(f'Successfully installed libraries')
except subprocess.CalledProcessError as e:
    print(f'Error installing libraries: {e}')

import arcade
import pathlib
import explosion as ex

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
        self.change_y = -1.5
    
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
        """
        Class constructor, initializes class attributes that are used throughout the class, calls setup
        Parameters:
            - self (HumanVsAI): This class instance
        Returns:
            None
        """
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
        # List of enemies shot by AI #2
        self.enemies_shot = []
        # Wave number, larger numbers are more difficult
        self.wave = 0
        # Tied to wave difficulty
        self.enemies_per_y = 1
        # Is the AI moving to its target?
        self.finding_target = False
        # Is the game over?
        self.game_over = 0
        #Counter for level 2 AI
        self.counter = 0
        #Target list for level 4 AI
        self.ai_targets = []
        # How long since player blew up, allows for explosion to finish before quitting
        self.time_since_game_over = 0
        self.setup()

    def setup(self):
        """
        Game setup, includes loading background and initializing player, AI player, score, and empty lists
        for enemies, missiles, and explosions then adds them all to scene
        Parameters:
            - self (HumanVsAI): This class instance
        
        Returns:
            None
        """
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
        """
        This function renders the state of the game regardless of what it is, leaves state unchanged

        Parameters:
            - self (HumanVsAI): This class instance
        
        Returns:
            None
        """
        arcade.start_render()
        # Clear the screen
        self.clear()

        # Draw the scene
        self.scene.draw()

        # Render the Score text
        arcade.draw_text(f"Score: {self.score}", 10, SCREEN_HEIGHT - 25, arcade.color.WHITE, 20)
        # Render the Wave text
        arcade.draw_text(f"Wave: {self.wave}", 380, SCREEN_HEIGHT - 25, arcade.color.WHITE, 20)
        # Render the AI Level text
        if self.wave//3+1 == 1:
            arcade.draw_text(f"Lvl {self.wave//3+1} AI: Random Shooting", 620, SCREEN_HEIGHT - 25, arcade.color.WHITE, 20)
        elif self.wave//3+1 == 2:
            arcade.draw_text(f"Lvl {self.wave//3+1} AI: Sweep", 620, SCREEN_HEIGHT - 25, arcade.color.WHITE, 20)
        elif self.wave//3+1 == 3:
            arcade.draw_text(f"Lvl {self.wave//3+1} AI: Lowest Enemy First", 620, SCREEN_HEIGHT - 25, arcade.color.WHITE, 20)
        elif self.wave//3+1 == 4:
            arcade.draw_text(f"Lvl {self.wave//3+1} AI: Sharpshooter", 620, SCREEN_HEIGHT - 25, arcade.color.WHITE, 20) 

    def on_update(self, delta_time):
        """
        This function updates the state of the game every tick, includes AI behavior, hit-box collision detection,
        enemy spawning, and checking if game is over

        Parameters:
            - self (HumanVsAI): This class instance
            - delta_time (float): Time since this function last ran
        
        Returns:
            None
        """
        if self.wave == 13:
            self.game_over = 2
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
            #Level 2 AI, shoot every 50 pixels back and forth
            elif self.wave < 6:
                if self.last_shot_ai + 0.35 < time.time():
                    self.ai_player.center_x = self.counter * 50 + 625
                    missiles.append(Missile(self.ai_player.center_x,self.ai_player.center_y+50))
                    self.last_shot_ai = time.time()
                    if self.counter == 0:
                        self.counter_adder = 1
                    elif self.counter == 9:
                        self.counter_adder = -1
                    self.counter += self.counter_adder
                    

            #Level 3 AI, shoot lowest enemy
            elif self.wave < 9:
                # Find lowest y-value enemy and manuever to shoot it
                if len(enemies) > 0 and not self.game_over:
                    first = True
                    for enemy in enemies:
                        # If enemy is in AI's game, has a y lower than lowest_y, hasn't already been shot at, and AI isn't currently
                        # moving to an enemy, enemy becomes lowest_y
                        # if enemy.center_y < self.lowest_y_pos[1] and enemy.center_x > 500 and not (enemy in self.enemies_shot)\
                        #     and enemy.center_y < 750 and not self.finding_target:
                        if enemy.center_y < 750 and enemy.center_x > 500:
                            if first:
                                self.lowest_y = enemy
                                first = False
                            elif enemy.center_y <= self.lowest_y.center_y and not (enemy in self.enemies_shot):
                                self.lowest_y = enemy
                    # lowest y is now enemy with lowest y position
                    self.lowest_y_pos = self.lowest_y.position
                    
                    # If AI player is to the left of enemy, move to the right
                    # If AI player is to the right of enemy, move to the left
                    # If AI player is underneath an enemy's hitbox, fire once then ignore that enemy
                    if self.ai_player.center_x < self.lowest_y_pos[0]-10:
                        self.ai_player.change_x = 5
                        self.finding_target = True
                    elif self.ai_player.center_x > self.lowest_y_pos[0]+10:
                        self.ai_player.change_x = -5
                        self.finding_target = True
                    elif not (self.lowest_y in self.enemies_shot):
                        self.ai_player.change_x = 0
                        missiles.append(Missile(self.ai_player.center_x,self.ai_player.center_y+50))
                        self.enemies_shot.append(self.lowest_y)
                        self.finding_target = False
                    self.ai_player.update()
            # Level 4 AI, shoots at all enemies, prioritizing lower ones
            elif self.wave <= 12:
                if len(enemies) > 0 and not self.game_over:
                    ai_enemies = []
                    # Gather all enemies on AI's game
                    for enemy in enemies:
                        if enemy.center_y < 750 and enemy.center_x > 500:
                            ai_enemies.append(enemy)
                    ai_enemies.sort(key= lambda x: x.center_y)
                    ai_enemies = list(filter(lambda e: not (e in self.enemies_shot),ai_enemies))
                    for enemy in ai_enemies:
                        if self.ai_player.center_x >= enemy.center_x-10 and self.ai_player.center_x <= enemy.center_x+10:
                            missiles.append(Missile(self.ai_player.center_x,self.ai_player.center_y+50))
                            self.enemies_shot.append(enemy)
                    ai_enemies = list(filter(lambda e: not (e in self.enemies_shot),ai_enemies))
                    if len(ai_enemies) > 0:
                        if self.ai_player.center_x < ai_enemies[0].center_x-10:
                                self.ai_player.change_x = 4
                        elif self.ai_player.center_x > ai_enemies[0].center_x+10:
                                self.ai_player.change_x = -4
                        self.ai_player.update()
                    
                



            # No enemies means the wave has been beaten, so move onto next wave and spawn the enemies
            if len(enemies) == 0:
                self.wave += 1
                # Ramp the difficulty by increasing enemies per why every 3 waves
                if self.wave % 3 == 0:
                    self.enemies_per_y  += 1
                # Spawn 3 + (2 * wave# % 3) * enemies_per_y enemies per wave
                for y in range(3+ 2*(self.wave%3)):
                    for x in range(self.enemies_per_y):
                        # Split the screen width depending on the enemies per y, spawning one enemy in each section
                        spawn_x = random.randrange(10*x//self.enemies_per_y, 10*(x+1)//self.enemies_per_y) * 50 + 25
                        spawn_x_ai = spawn_x+600
                        # every 200 pixels is a new y level
                        enemies.extend([Enemy(spawn_x,SCREEN_HEIGHT+200*y),Enemy(spawn_x_ai,SCREEN_HEIGHT+200*y)])
                        # enemies.extend([Enemy(spawn_x_ai,SCREEN_HEIGHT+200*y)]) # AI enemies only for testing
                        

            # If enemy and missile are colliding, destroy them both, create explosion
            # then check if any enemies have reached the player to end the game
            for enemy in enemies:
                for missile in missiles:
                    if enemy.collides_with_sprite(missile):
                        enemy.kill()
                        missile.kill()
                        # If a player kill, increase score
                        if enemy.center_x <= 500:
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
                        # Adds a particle to the explosion, number of particles determined by preset value
                        explosions_list = self.scene.get_sprite_list('explosions')
                        particle_e = ex.Particle(explosions_list)
                        particle_e.position = enemy.position
                        particle_p = ex.Particle(explosions_list)
                        particle_p.position = player.position
                        explosions_list.append(particle_e)
                        explosions_list.append(particle_p)
                    #Smoke is added with a size of 50 pixels at explosion site
                    smoke_e = ex.Smoke(50)
                    smoke_p = ex.Smoke(50)
                    smoke_e.position = enemy.position
                    smoke_p.position = player.position
                    explosions_list.append(smoke_e)
                    explosions_list.append(smoke_p)
                    # Enemy and Player are removed from SpriteList (no longer displayed)
                    enemy.kill()
                    player.kill()

            # Missiles and enemies update regardless of player movement
            self.scene.update(['enemies','missiles','explosions'])
        else:
            # If game has been over for 2 seconds, display GameOver screen, window must be resized for new screen
            game_over_view = GameOverView(self.score,self.wave, self.game_over)
            self.window.set_size(480,710)
            self.window.show_view(game_over_view)

    def on_key_press(self, key, modifiers):
        """
        Sets player movement to left and right arrow keys, Space to shoot missiles, and Escape to pause and quit to menu
        Parameters:
            - self (HumanVsAI): This class instance
            - key (arcade.key): key being released
            - modifiers: extra state of key being released (Ex. Caps Lock or holding Shift/Ctrl)
        
        Returns:
            None
        """
        if key == arcade.key.LEFT:
            # Movement to the left is in the -x direction
            self.player.change_x = -5
        elif key == arcade.key.RIGHT:
            # Movement to the right is in the +x direction
            self.player.change_x = 5
        elif key == arcade.key.SPACE:
            # Ensure a 0.5 second delay between missile firing
            if self.last_shot <= time.time() - 0.5:
                self.scene.get_sprite_list('missiles').append(Missile(self.player.center_x,self.player.center_y+50))
                self.last_shot = time.time()
        elif key == arcade.key.ESCAPE:
            #Pause and quit to menu
            title_view = TitleView(self)
            self.window.set_size(480,710)
            self.window.show_view(title_view)
            

    def on_key_release(self, key, modifiers):
        """
        Sets player movement to 0 when left or right arrow key is released
        Parameters:
            - self (HumanVsAI): This class instance
            - key (arcade.key): key being released
            - modifiers: extra state of key being released (Ex. Caps Lock or holding Shift/Ctrl)
        
        Returns:
            None
        """
        if key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player.change_x = 0

# Title screen
class TitleView(arcade.View):
    def __init__(self, paused_game = None) -> None:
        """
        Class constructor, initializes class attributes that are used throughout the class
        Parameters:
            - self (TitleView): This class instance
        Returns:
            None
        """
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
        """
        This function updates the state of the menu every tick, used for blinking text on screen

        Parameters:
            - self (TitleView): This class instance
            - delta_time (float): Time since this function last ran
        
        Returns:
            None
        """
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
        """
        This function renders the state of the menu, includes background image, title text, and instructional text
        text shown depends on state of boolean variables determined in on_update and on_key_press

        Parameters:
            - self (TitleView): This class instance
        
        Returns:
            None
        """
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
                "Controls:",
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
                "   - ESC to pause and quit to title", start_x=30, start_y=210, color=arcade.color.FLORAL_WHITE, font_size=20
            )
            arcade.draw_text(
                "Gain score for each enemy destroyed", start_x=30, start_y=180, color=arcade.color.FLORAL_WHITE, font_size=20
            )
            arcade.draw_text(
                "Lvl of the AI increases every 3 waves", start_x=30, start_y=150, color=arcade.color.FLORAL_WHITE, font_size=20
            )
            arcade.draw_text(
                "Goal", start_x=30, start_y=120, color=arcade.color.FLORAL_WHITE, font_size=20
            )
            arcade.draw_text(
                "   - Survive all 4 levels of AI", start_x=30, start_y=90, color=arcade.color.FLORAL_WHITE, font_size=20
            )
            arcade.draw_text(
                "           Press ESC to return", start_x=30, start_y=60, color=arcade.color.RED, font_size=20
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
        """
        Detects Space to start or resume game depending on boolean variable, R to restart if paused, I to show instructions
        Parameters:
            - self (TitleView): This class instance
            - key (arcade.key): key being released
            - modifiers: extra state of key being released (Ex. Caps Lock or holding Shift/Ctrl)
        
        Returns:
            None
        """
        # If menu isn't shown during a game, only show detect Space (start) and I (instructions)
        # If game is paused, detect Space (resume), I (instructions), and R (restart)
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
        """
        Class constructor, initializes class attributes that are used throughout the class
        Parameters:
            - self (TitleView): This class instance
        Returns:
            None
        """
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
        """
        This function updates the state of the GameOver menu every tick, used for blinking text on screen

        Parameters:
            - self (GameOverView): This class instance
            - delta_time (float): Time since this function last ran
        
        Returns:
            None
        """
        # First, count down the time
        self.display_timer -= delta_time

        # If the timer has run out, toggle text
        if self.display_timer < 0:
            self.show_text = not self.show_text
            # And reset the timer so the text flashes slowly
            self.display_timer = 2

    def on_draw(self) -> None:
        """
        This function renders the state of the GameOver screen including defeat or victory text, final score, wave reached, 
        and level of AI reached before death. Shows a flashing option to return to menu

        Parameters:
            - self (GameOverView): This class instance
        
        Returns:
            None
        """
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
            if self.wave/3+1 < 4:
                arcade.draw_text(
                            f"   You Beat The Lvl {self.wave//3+1} AI!",
                            start_x=30,
                            start_y=335,
                            color=arcade.color.MINT_GREEN,
                            font_size=26,
                        )
            else:
                arcade.draw_text(
                            f"     You Survived Every AI!",
                            start_x=30,
                            start_y=335,
                            color=arcade.color.MINT_GREEN,
                            font_size=26,
                        )
        else:
            arcade.draw_text(
                        f"        The Lvl {self.wave//3+1} AI Wins...",
                        start_x=30,
                        start_y=335,
                        color=arcade.color.RED_DEVIL,
                        font_size=26,
                    )
        arcade.draw_text(
                    f"                 Score: {self.score}",
                    start_x=30,
                    start_y=250,
                    color=arcade.color.FLORAL_WHITE,
                    font_size=22,
                )
        arcade.draw_text(
                    f"                 Wave: {self.wave}",
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
        """
        Detects Escape to return to TitleView
            - self (GameOverView): This class instance
            - key (arcade.key): key being released
            - modifiers: extra state of key being released (Ex. Caps Lock or holding Shift/Ctrl)
        
        Returns:
            None
        """
        if key == arcade.key.ESCAPE:
            title_view = TitleView()
            self.window.show_view(title_view)
            

def main():
    # Create menu window
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "HumanVsAi")
    # Set window to show a TitleView
    title_view = TitleView()
    window.show_view(title_view)
    # Start running the active View (starts updating state every tick)
    arcade.run()

if __name__ == "__main__":
    main()
