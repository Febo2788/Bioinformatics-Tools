from docx import Document
import cv2
import numpy as np
from collections import deque
from PIL import ImageGrab, Image
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import io
import win32clipboard
from rich.progress import Progress


def standardize_colors(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray[gray != 0] = 255
    return gray

def detect_arrows(img):
    height, width = img.shape
    middle_row = height // 2
    arrows = []
    in_arrow = False
    for i in range(width):
        pixel = img[middle_row, i]
        if not in_arrow and pixel == 255:
            in_arrow = True
            arrow_start = i
        elif in_arrow and pixel != 255:
            in_arrow = False
            arrow_end = i - 1
            arrows.append((arrow_start, arrow_end))
    return arrows

def assign_colors(img, arrows, colors):
    colored_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    middle_row = img.shape[0] // 2
    extra_arrows = 0
    extra_arrow_color = '#FF0000'  # Default extra arrow color
    for i, (start, end) in enumerate(arrows):
        color = colors[i % len(colors)]  # Use modulo to alternate colors
        bgr_color = tuple(int(color[j+1:j+3], 16) for j in (4, 2, 0))
        for j in range(start, end + 1):
            colored_img[middle_row, j] = bgr_color
            y = middle_row
            while y < img.shape[0] and img[y, j] != 0:
                colored_img[y, j] = bgr_color
                y += 1
            y = middle_row - 1
            while y >= 0 and img[y, j] != 0:
                colored_img[y, j] = bgr_color
                y -= 1
    return colored_img, extra_arrows

def color_remaining_pixels(img):
    height, width, _ = img.shape
    dx = [-1, 0, 1, 0]
    dy = [0, 1, 0, -1]
    visited = np.zeros((height, width), dtype=bool)
    queue = deque()
    
    # Create a progress bar for this function
    with Progress() as progress:
        task = progress.add_task("[cyan]Coloring pixels...", total=width * height)

        for x, y in [(x, y) for x in range(width) for y in range(height)]:
            if np.array_equal(img[y, x], [255, 255, 255]) and not visited[y, x]:
                for i in range(4):
                    nx, ny = x + dx[i], y + dy[i]
                    if 0 <= nx < width and 0 <= ny < height and not np.array_equal(img[ny, nx], [0, 0, 0]) and not np.array_equal(img[ny, nx], [255, 255, 255]):
                        queue.append((x, y))
                        color = img[ny, nx]
                        break
                while queue:
                    px, py = queue.pop()
                    img[py, px] = color
                    visited[py, px] = True
                    for i in range(4):
                        nx, ny = px + dx[i], py + dy[i]
                        if 0 <= nx < width and 0 <= ny < height and not visited[ny, nx] and np.array_equal(img[ny, nx], [255, 255, 255]):
                            queue.append((nx, ny))
            progress.update(task, advance=1)
    return img


def process_image_blue_red(colors, copy_callback):
    # Similar to process_image but simplified for blue and red only
    try:
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            open_cv_image = standardize_colors(open_cv_image)
            arrows = detect_arrows(open_cv_image)
            colored_img, _ = assign_colors(open_cv_image, arrows, colors)
            pil_img = Image.fromarray(cv2.cvtColor(colored_img, cv2.COLOR_BGR2RGB))
            copy_callback(pil_img)
            print("Done with Blue and Red pattern!")
        else:
            messagebox.showerror("Error", "No image found in the clipboard!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def add_colors():
    root = tk.Tk()
    root.withdraw()
    user_input = messagebox.askyesno("Question", "Would you like to add more colors? Select no to proceed with the default 7.")
    colors = ['#FFF200', '#B3FF50', '#FF8E55', '#33E8B2', '#7D3C98', '#ED028C', '#BCBDC0']
    if user_input:
        new_colors = simpledialog.askstring("Input", "Provide the hex color codes for each color you'd like to add, if there's multiple separate them with commas.")
        if new_colors:
            new_colors = new_colors.split(',')
            colors.extend(new_colors)
        color_dict = {i+1: colors[i] for i in range(len(colors))}
        color_message = "\n".join([f"{k}: {v}" for k, v in color_dict.items()])
        messagebox.showinfo("Color Assignments", f"The hex color codes along with their # assignments are shown below:\n\n{color_message}")
    return colors

def copy_image_to_clipboard(pil_img):
    output = io.BytesIO()
    pil_img.save(output, format='BMP')
    data = output.getvalue()[14:]  # BMP file header offset for DIB
    output.close()

    win32clipboard.OpenClipboard()  # Open the clipboard
    win32clipboard.EmptyClipboard()  # Clear the clipboard
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)  # Set the clipboard data
    win32clipboard.CloseClipboard()  # Close the clipboard

def process_image(colors, copy_callback):
    try:
        # Get the image from the clipboard
        img = ImageGrab.grabclipboard()
        if isinstance(img, Image.Image):
            # Convert PIL Image to OpenCV Image
            open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            open_cv_image = standardize_colors(open_cv_image)

            arrows = detect_arrows(open_cv_image)
            num_arrows = len(arrows)
            print(f"  -> Detected {num_arrows} arrows.")

            word_doc_path = filedialog.askopenfilename(title="Select a Word document", filetypes=(("Word documents", "*.docx"), ("All files", "*.*")))
            if word_doc_path:
                doc = Document(word_doc_path)
                color_dict = {i+1: colors[i] for i in range(len(colors))}
                arrow_colors = [color_dict[int(paragraph.text)] for paragraph in doc.paragraphs if paragraph.text.isdigit()]

                colored_img, extra_arrows = assign_colors(open_cv_image, arrows, arrow_colors)
                if extra_arrows:
                    print(f"  -> There were {extra_arrows} extra arrows, which have been colored red.")

                colored_img = color_remaining_pixels(colored_img)
                pil_img = Image.fromarray(cv2.cvtColor(colored_img, cv2.COLOR_BGR2RGB))
                copy_callback(pil_img)
                print("Done!")
        else:
            messagebox.showerror("Error", "No image found in the clipboard!")
    except Exception as e:
        messagebox.showerror("Error", str(e))


def main():
    root = tk.Tk()
    root.withdraw()

    # Define the copy callback function here so it's available for later use.
    def copy_callback(img):
        if messagebox.askyesno("Copy to Clipboard", "Copy the output image to the clipboard?"):
            copy_image_to_clipboard(img)

    # Prompt user for the color mode choice
    choice = messagebox.askquestion("Color Mode", "Do you want to use the blue and red pattern? (Select no to begin adding colors)")

    # Set the function based on choice
    if choice == "yes":
        colors = ['#0000FF', '#FF0000']  # Blue and Red
        process_func = lambda: process_image_blue_red(colors, copy_callback)
    else:
        colors = add_colors()
        process_func = lambda: process_image(colors, copy_callback)

    root.deiconify()
    root.title("Image Processing")
    root.geometry("400x200")

    # Set up button to process image
    btn_process = tk.Button(root, text="Process Image", command=process_func)
    btn_process.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
