import arcade
import pathlib
import math

# Constants
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 750
PLAYER_RADIUS = 50
MAP_SCALING = 1.0

ASSETS_PATH = str(pathlib.Path(__file__).resolve().parent) + '/assets'

class Player(arcade.Sprite):
    def __init__(self):
        super().__init__(ASSETS_PATH+'/fighter.png')  # Replace with your player sprite file
        self.center_x = SCREEN_WIDTH // 2
        self.center_y = SCREEN_HEIGHT // 2

class MyGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)
        arcade.set_background_color(arcade.color.BLACK)

        self.scene = None
        self.player = None
        self.setup()

    def setup(self):
        # Get file path to TileMap
        map_path = ASSETS_PATH + '/galaga_map.tmx'

        # Camera setup
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

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

        print(self.tile_map.object_lists['game_borders'][0].shape)

        # Initialize score
        self.score = 0

        # Initialize player
        self.player = Player()
        self.scene.add_sprite('player',self.player)


        
    def on_draw(self):
        arcade.start_render()
        # Clear the screen
        self.clear()

        # Draw the scene
        self.scene.draw()


    def on_update(self, delta_time):
        self.player.update()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.UP:
            self.player.change_y = 5
        elif key == arcade.key.DOWN:
            self.player.change_y = -5
        elif key == arcade.key.LEFT:
            self.player.change_x = -5
        elif key == arcade.key.RIGHT:
            self.player.change_x = 5

    def on_key_release(self, key, modifiers):
        if key == arcade.key.UP or key == arcade.key.DOWN:
            self.player.change_y = 0
        elif key == arcade.key.LEFT or key == arcade.key.RIGHT:
            self.player.change_x = 0

def main():
    window = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT, "My Arcade Game")
    arcade.run()

if __name__ == "__main__":
    main()
