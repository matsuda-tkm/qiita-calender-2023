from PIL import Image
import glob

frames = []
imgs = glob.glob("./data/*.png")
for i in imgs:
    new_frame = Image.open(i)
    frames.append(new_frame)

frames[0].save('animation.gif', format='GIF', append_images=frames[1:], save_all=True, duration=50, loop=0, optimize=True)