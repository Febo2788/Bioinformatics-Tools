from PIL import Image

image_path = "C:\\Users\\thora\\Downloads\\coloring folder\\image that needs to be resized.png"
image = Image.open(image_path)

desired_width = 3829
desired_height = 138
resized_image = image.resize((desired_width, desired_height), Image.LANCZOS)

resized_image_path = "C:\\Users\\thora\\Downloads\\coloring folder\\resized_image.png"
resized_image.save(resized_image_path)

print(f"Image has been resized and saved to: {resized_image_path}")
