# In the future, run on the web like itch.io, gamejolt, etc
import contextlib
with contextlib.redirect_stdout(None):
    import pygame
import os
import random
import asyncio

# Screen settings: width and height
SCREEN_WIDTH = 500
SCREEN_HEIGHT = 800

# pygame.transform.scale2x: Doubles the image size
# pygame.image.load: Loads the image and saves it to the variable
PIPE_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'pipe.png')))
GROUND_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'base.png')))
BACKGROUND_IMAGE = pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bg.png')))
BIRD_IMAGES = [
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird1.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird2.png'))),
    pygame.transform.scale2x(pygame.image.load(os.path.join('imgs', 'bird3.png')))
]

# Game settings (FPS, etc.)
pygame.font.init()
FONT_POINTS = pygame.font.SysFont('arial', 50)

class Bird:
    IMGS = BIRD_IMAGES
    # Bird animation
    MAX_ROTATION = 25
    ROTATION_VELOCITY = 20
    ANIMATION_TIME = 5

    # Creating a constructor for the Bird class in the game
    def __init__(self, x, y):
        self.x = x # Bird's x position
        self.y = y # Bird's y position
        self.angle = 0 # Bird's rotation angle
        self.velocity = 0 # Bird's speed
        self.height = self.y # Bird's height
        self.time = 0 # Bird's time
        self.image_count = 0 # Image count for the bird
        self.image = self.IMGS[0] # Bird's initial image
    
    # Method for the bird to jump
    def jump(self):
        # Makes the bird jump upwards (negative, as the screen is inverted)
        self.velocity = -10.5
        self.time = 0  # Time when the bird jumped
        self.height = self.y # Bird's height when it jumped

    # Method to move the bird on the game screen
    def move(self):
        # Calculate the displacement
        self.time += 1 # Increment bird's time
        displacement = 0 + self.velocity * self.time + 1.5 * (self.time**2) # Calculates the bird's displacement (equation of motion: S=So + Vot + (at^2)/2)

        # Restrict displacement
        if displacement > 16: # If the displacement is greater than 16 (fall limit), don't let the bird fall faster
            displacement = 16 
        elif displacement < 0: # If the displacement is less than 0 (jump limit), don't let the bird ascend faster
            displacement -= 2 # Higher jump when jumping
        
        self.y = self.y + displacement # Update bird's position

        # Bird's angle - Animation
        if displacement < 0 or self.y < (self.height + 50): # If the bird is rising or above the initial jump height
            if self.angle < self.MAX_ROTATION: # Maximum rotation for the bird tilted upward
                self.angle = self.MAX_ROTATION
        else:
            if self.angle > -90: # Maximum rotation for the bird tilted downward
                self.angle -= self.ROTATION_VELOCITY
    
    # Method to draw the bird on the game screen 
    def draw(self, screen):
        # Define which bird image to use
        self.image_count += 1
        # Bird animation - Flap wings so that every 5 frames (ANIMATION_TIME) the bird's image changes (Open and close wings)
        if self.image_count < self.ANIMATION_TIME: # If the image count is less than the animation time, the bird's image is the first
            self.image = self.IMGS[0] 
        elif self.image_count < self.ANIMATION_TIME*2: # If the image count is less than animation time*2(10), the bird's image is the second
            self.image = self.IMGS[1]
        elif self.image_count < self.ANIMATION_TIME*3: # If the image count is less than animation time*3(15), the bird's image is the third
            self.image = self.IMGS[2]
        elif self.image_count < self.ANIMATION_TIME*4: # If the image count is less than animation time*4(20), the bird's image is the second
            self.image = self.IMGS[1]
        elif self.image_count == self.ANIMATION_TIME*4 + 1: # If the image count is equal to animation time*4 + 1(21), the bird's image is the first
            self.image = self.IMGS[0]
            self.image_count = 0 # Resets the image count
        
        # If the bird is falling, don't flap wings
        if self.angle <= -80: # If the bird's angle is less than or equal to -80, the bird's image is the second
            self.image = self.IMGS[1]
            self.image_count = self.ANIMATION_TIME*2 # So the bird's wings stay closed, and when it jumps, the wings open
        
        # Draw the bird
        rotated_image = pygame.transform.rotate(self.image, self.angle) # Rotate the bird image according to the bird's angle with rotate(image, angle)
        center_image_position = self.image.get_rect(topleft=(self.x, self.y)).center # Get the center of the original bird image to paste the rotated image at the center
        rectangle = rotated_image.get_rect(center=center_image_position) # Create a rectangle for the rotated bird image and paste it in the center of the original image
        screen.blit(rotated_image, rectangle.topleft) # Paste the rotated image at the center of the original image, screen.blit = paste on the screen

    # Method to get the bird's mask (collision) - To know if there was a collision between the bird and the pipes
    def get_mask(self):
        return pygame.mask.from_surface(self.image) # Return the mask of the bird's image

class Pipe:
    DISTANCE = 200 # Distance between pipes
    SPEED = 5 # Pipe speed 

    # Creating a constructor for the Pipe class in the game, to define the x position of the pipe and the height of the pipe
    def __init__(self, x): # Constructor for the Pipe class, only the x position of the pipe, as the y position is random
        self.x = x # x position of the pipe 
        self.height = 0 # Height of the pipe
        self.top_position = 0 # Position of the top pipe
        self.bottom_position = 0 # Position of the bottom pipe
        # .flip(image, horizontal, vertical) - Flips the image, horizontal = False, vertical = True
        self.TOP_PIPE = pygame.transform.flip(PIPE_IMAGE, False, True) # Flips the top pipe image to be upside down 
        self.BOTTOM_PIPE = PIPE_IMAGE
        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450) # Random height between 50 and 450 so the bird can pass between the pipes, whether jumping or falling
        self.top_position = self.height - self.TOP_PIPE.get_height() # Top pipe position, get_height() gets the pipe image's height
        self.bottom_position = self.height + self.DISTANCE

    def move(self):
        self.x -= self.SPEED # Moves the pipe to the left (negative)

    def draw(self, screen):
        screen.blit(self.TOP_PIPE, (self.x, self.top_position)) # Draws the top pipe on the screen
        screen.blit(self.BOTTOM_PIPE, (self.x, self.bottom_position)) # Draws the bottom pipe on the screen

    def collide(self, bird):
        bird_mask = bird.get_mask() # Get the bird's mask (collision) 
        top_mask = pygame.mask.from_surface(self.TOP_PIPE) # Get the top pipe's mask (collision) 
        bottom_mask = pygame.mask.from_surface(self.BOTTOM_PIPE) # Get the bottom pipe's mask (collision)

        top_distance = (self.x - bird.x, self.top_position - round(bird.y)) # Distance between the top pipe and the bird
        bottom_distance = (self.x - bird.x, self.bottom_position - round(bird.y)) # Distance between the bottom pipe and the bird

        top_collision_point = bird_mask.overlap(top_mask, top_distance) # Collision point between the bird and the top pipe, to check if both have a common pixel
        bottom_collision_point = bird_mask.overlap(bottom_mask, bottom_distance) # Collision point between the bird and the bottom pipe, to check if both have a common pixel

        if top_collision_point or bottom_collision_point: # If there's a collision between the bird and either the top or bottom pipe
            return True
        else:
            return False

class Ground:
    SPEED = 5
    WIDTH = GROUND_IMAGE.get_width() # Width of the ground image 
    IMAGE = GROUND_IMAGE # Ground image

    def __init__(self, y): # Constructor for the Ground class, to define the y position of the ground
        self.y = y
        self.x1 = 0 # x position of ground 1
        self.x2 = 0 + self.WIDTH # x position of ground 2

    def move(self):
        self.x1 -= self.SPEED # Moves ground 1 to the left
        self.x2 -= self.SPEED # Moves ground 2 to the left

        if self.x1 + self.WIDTH < 0: # If ground 1 moves off the screen
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0: # If ground 2 moves off the screen
            self.x2 = self.x1 + self.WIDTH 
    
    def draw(self, screen):
        screen.blit(self.IMAGE, (self.x1, self.y))
        screen.blit(self.IMAGE, (self.x2, self.y))

def draw_screen(screen, birds, pipes, ground, points): # Function to draw the game screen
    screen.blit(BACKGROUND_IMAGE, (0, 0)) # Draw the background on the screen

    for bird in birds: # For each bird in the list of birds
        bird.draw(screen) # Draw the bird on the screen
    
    for pipe in pipes: # For each pipe in the list of pipes
        pipe.draw(screen) # Draw the pipes on the screen

    text = FONT_POINTS.render("Gopi: " + str(points), 1, (255, 255, 255)) # Render the "Gopi" text on the screen
    
    screen.blit(text, (SCREEN_WIDTH - 10 - text.get_width(), 10)) # Draw the "Gopi" text on the screen

    ground.draw(screen) # Draw the ground on the screen
    pygame.display.update() # Update the screen



# Main game function
def simulate(inputs):
    random.seed(1337)
    # Initialize the game, passing the width and height of the screen for each game element to each class and function
    birds = [Bird(230, 350)] # List of birds in the game
    ground = Ground(730) # Ground object
    pipes = [Pipe(700)] # List of pipes in the game
    points = 0 # Game score
    aktTime = 0
    running = True # Variable to check if the game is running
    cnt = 0
    x = 0
    frameTime = 0
    while running: # While the game is running
        if points >= 0 and points < 10:
            x = 25 # Game FPS
        elif points >= 10 and points < 20:
            x = 27
        elif points >= 20 and points < 30:
            x = 29
        elif points >= 30 and points < 40:
            x = 31
        elif points >= 40 and points < 50:
            x = 33
        elif points >= 50 and points < 100:
            x = 34
        elif points >= 100:
            x = 40

        frameTime = 1/x - 0.0001 #magic because of non equal frame length...
        if cnt < len(inputs):
            if inputs[cnt] < aktTime + frameTime: #in this frame a jump was triggered
                cnt += 1
                for bird in birds:
                    bird.jump() # The bird jumps by calling the jump() function
        # Bird movement
        for bird in birds:
            bird.move()
        
        # Ground movement
        ground.move()

        # Pipe movement
        remove_pipe = []
        add_pipe = False
        for pipe in pipes:
            pipe.move()
            

            for i, bird in enumerate(birds): # For each bird in the list of birds
                if pipe.collide(bird): # If the bird collides with the pipe
                    birds.pop(i) # Remove the bird from the list of birds
                if not pipe.passed and bird.x > pipe.x: # If the bird passes the pipe
                    pipe.passed = True
                    add_pipe = True
            pipe.move()
            if pipe.x + pipe.TOP_PIPE.get_width() < 0: # If the pipe moves off the screen
                remove_pipe.append(pipe)

        if add_pipe: # If a pipe is added
            points += 1 # Increment the score
            pipes.append(Pipe(600)) # Add a new pipe on the screen

        for pipe in remove_pipe:
            pipes.remove(pipe) # Remove the pipe from the list of pipes

        for i, bird in enumerate(birds):
            if (bird.y + bird.image.get_height()) > ground.y or bird.y < 0: # If the bird touches the ground or the ceiling
                birds.pop(i) # Remove the bird from the list of birds

        if len(birds) == 0:
            running = False
        aktTime += frameTime
    return points





if __name__ == "__main__":
    inputs = [0.0, 0.8491907119750977, 1.4142272472381592, 1.8989994525909424, 2.4258410930633545, 2.9903972148895264, 3.43713641166687, 4.1636269092559814, 4.730172872543335, 5.296604871749878, 5.821712017059326, 6.062922954559326, 6.224619626998901, 6.709406137466431, 7.640908718109131, 8.043145179748535, 8.811955213546753, 9.216413021087646, 9.6601881980896, 10.546671390533447, 10.95087456703186, 11.435769319534302, 11.920541048049927, 12.122118473052979, 12.282597303390503]
    print(simulate(inputs))