import pygame
import time

pygame.mixer.init()

print("Playing sound...")

pygame.mixer.music.load("sounds/peppaping_heyhowareyou.mp3")   # <-- put your file here
pygame.mixer.music.play()

# wait until sound finishes
while pygame.mixer.music.get_busy():
    time.sleep(0.1)

print("Done.")
