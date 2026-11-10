#THIS IS FROM CHATGPT AT LEAST GIVE IT A ONCE OVER AND SOME THOROUGH TESTINGs
import pygame
import json
import time
import subprocess
import os

MOUTH_PATH = "./mouths/"
AUDIO_PATH = "my_audio.wav"
VISEME_PATH = "visemes.json"
WINDOW_SIZE = (240, 240)  # Adjust based on your display

# Load viseme sequence from Rhubarb
def load_visemes(path):
    with open(path, 'r') as f:
        return json.load(f)

# Initialize Pygame
def init_display():
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("Lip Sync Character")
    return screen

# Load all viseme images into memory
def load_mouth_images():
    return {v: pygame.image.load(os.path.join(MOUTH_PATH, f"{v}.png")) for v in "ABCDEFEX"}

# Play audio (non-blocking)
def play_audio(path):
    subprocess.Popen(["aplay", path])

# Display viseme on screen
def render_viseme(screen, image):
    screen.fill((0, 0, 0))
    screen.blit(image, (0, 0))
    pygame.display.flip()

# Sync visemes to playback
def animate(screen, visemes, mouth_images):
    start = time.time()
    viseme_index = 0

    while viseme_index < len(visemes):
        now = time.time() - start
        current_viseme = visemes[viseme_index]

        # If it’s time for the next viseme
        if now >= current_viseme["time"]:
            mouth = current_viseme["mouth"]
            if mouth in mouth_images:
                render_viseme(screen, mouth_images[mouth])
            viseme_index += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        pygame.time.wait(5)  # Light wait to prevent CPU overload

# Main sequence
def main():
    screen = init_display()
    visemes = load_visemes(VISEME_PATH)
    mouth_images = load_mouth_images()

    print("🔊 Playing audio + animating visemes...")
    play_audio(AUDIO_PATH)
    animate(screen, visemes, mouth_images)

    print("✅ Done. Waiting for window close...")
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
        pygame.time.wait(50)

if __name__ == "__main__":
    main()


#fullscreen
pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
