from spherov2 import scanner
from spherov2.sphero_edu import SpheroEduAPI
from pynput import keyboard
from spherov2.types import Color




toy = scanner.find_toy(toy_name="SB-AAAD") # Your name here
with SpheroEduAPI(toy) as api:
   # Visually show connection to sphero
   api.set_main_led(Color(r=0, g=255, b=0))
   api.spin(360, 1)


   up_pressed = False
   down_pressed = False
   left_pressed = False
   right_pressed = False


   api.set_heading(0)


   def on_press(key):
       # PRESS ESCAPE 'esc' TO EXIT PROGRAM
       if key == keyboard.Key.esc:
           return False
      
       speed = 50


       global up_pressed
       global down_pressed
       global left_pressed
       global right_pressed
       if key == keyboard.Key.up and not up_pressed:
           up_pressed = True
           api.set_speed(speed)           
       elif key == keyboard.Key.down and not down_pressed:
           down_pressed = True
           api.set_heading(api.get_heading()+180)
           api.set_speed(speed)           
       if key == keyboard.Key.left and not left_pressed:
           left_pressed = True
           api.set_heading(api.get_heading()-45)
       if key == keyboard.Key.right and not right_pressed:
           right_pressed = True
           api.set_heading(api.get_heading()+45)


   def on_release(key):
       global up_pressed
       global down_pressed
       global left_pressed
       global right_pressed


       if key == keyboard.Key.up:
           up_pressed = False
           api.set_speed(0)           
       elif key == keyboard.Key.down:
           down_pressed = False
           api.set_speed(0)           
       elif key == keyboard.Key.left:
           left_pressed = False        
       elif key == keyboard.Key.right:
           right_pressed = False
  
   with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
       listener.join()