from PIL import Image

# Load your original PNG (make sure it's high resolution, e.g. 512x512)
img = Image.open("icon.png")

# Save as .ico with multiple sizes
img.save("sortly_icon_fixed.ico", sizes=[(16,16), (32,32), (48,48), (256,256)])
