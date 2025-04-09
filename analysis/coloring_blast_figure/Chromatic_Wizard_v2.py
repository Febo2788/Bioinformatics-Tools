import pandas as pd
import cv2
import numpy as np
from collections import deque
from PIL import Image, ImageGrab
from tkinter import filedialog, messagebox, Tk, Button
from rich.progress import Progress
import io
import win32clipboard

# Set the maximum allowed image size to avoid the decompression bomb error
Image.MAX_IMAGE_PIXELS = None

# Store clicked points
selected_points = []

def standardize_colors(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray[gray >= 85] = 255
    gray[gray < 85] = 0
    return gray

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        selected_points.append((x, y))
        print(f"Point selected at: ({x}, {y})")

def detect_arrows_from_point(img, start_x):
    height, width = img.shape
    middle_row = height // 2
    arrows = []
    in_arrow = False
    for i in range(start_x, width):
        pixel = img[middle_row, i]
        if not in_arrow and pixel == 255:
            in_arrow = True
            arrow_start = i
        elif in_arrow and pixel != 255:
            in_arrow = False
            arrow_end = i - 1
            boundary = arrow_end + 1
            while boundary < width and img[middle_row, boundary] != 255:
                boundary += 1
            arrows.append((arrow_start, arrow_end, boundary))
    return arrows

def color_pour_in(img, start_x, start_y, bgr_color):
    queue = deque([(start_y, start_x)])
    visited = set()
    while queue:
        y, x = queue.popleft()
        if (y, x) not in visited and 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
            if np.array_equal(img[y, x], [255, 255, 255]):
                img[y, x] = bgr_color
                visited.add((y, x))
                for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ny, nx = y + dy, x + dx
                    if (ny, nx) not in visited and 0 <= nx < img.shape[1] and 0 <= ny < img.shape[0]:
                        if not np.array_equal(img[ny, nx], [0, 0, 0]):
                            queue.append((ny, nx))

def assign_colors(img, arrows, colors):
    colored_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    middle_row = img.shape[0] // 2
    pour_in_count = 0  # Counter for color pour-in regions

    with Progress() as progress:
        task = progress.add_task("[cyan]Filling arrows...", total=len(arrows))
        for i, (start, end, boundary) in enumerate(arrows):
            color = colors[i % len(colors)]
            bgr_color = tuple(int(color[j+1:j+3], 16) for j in (4, 2, 0))
            anchor_x = (start + end) // 2
            anchor_y = middle_row
            color_pour_in(colored_img, anchor_x, anchor_y, bgr_color)
            pour_in_count += 1  # Increment for each pour-in operation
            progress.update(task, advance=1)

    print(f"Number of color pour-in regions: {pour_in_count}")  # Print total regions filled
    return colored_img

def process_image_from_image(colors, pil_img, output_path):
    try:
        selected_points.clear()
        open_cv_image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
        open_cv_image = standardize_colors(open_cv_image)
        cv2.imshow("Select Starting Points", open_cv_image)
        cv2.setMouseCallback("Select Starting Points", mouse_callback)
        print("Please click on the image to select the starting points and press 'enter' when done.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        if not selected_points:
            print("No points were selected!")
            return
        for (start_x, start_y) in selected_points:
            arrows = detect_arrows_from_point(open_cv_image, start_x)
            print(f"Detected {len(arrows)} arrows.")  # Print number of arrows detected
            open_cv_image = assign_colors(open_cv_image, arrows, colors)
        pil_img_result = Image.fromarray(cv2.cvtColor(open_cv_image, cv2.COLOR_BGR2RGB))
        pil_img_result.save(output_path)
        print("Done! Output saved at:", output_path)
        return pil_img_result
    except Exception as e:
        print("Error:", str(e))

def copy_image_to_clipboard(pil_img):
    output = io.BytesIO()
    pil_img.save(output, format='BMP')
    data = output.getvalue()[14:]  # BMP format requires skipping the first 14 bytes
    output.close()

    # Use win32clipboard to copy to the clipboard
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
    win32clipboard.CloseClipboard()

def main():
    root = Tk()
    root.title("Image Processor")

    def process_clipboard_image():
        # Get image from clipboard
        pil_img = ImageGrab.grabclipboard()
        if pil_img is None:
            messagebox.showerror("Error", "No image found in clipboard!")
            return

        # Get Excel file with colors
        excel_path = filedialog.askopenfilename(title="Select the Excel file with colors", filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*")))
        if not excel_path:
            print("No Excel file selected!")
            return
        try:
            df = pd.read_excel(excel_path)
            colors = df['Hex Code'].tolist()
        except Exception as e:
            print(f"Failed to read colors from Excel: {e}")
            return

        # Process the image
        output_path = r"C:\Users\thora\Downloads\O118_Phages_EasyFig_colored.png"
        pil_img_processed = process_image_from_image(colors, pil_img, output_path)

        # Ask if the user wants to copy the output image to the clipboard
        if pil_img_processed and messagebox.askyesno("Copy to Clipboard", "Do you want to copy the output image to the clipboard?"):
            copy_image_to_clipboard(pil_img_processed)

    process_button = Button(root, text="Process Image from Clipboard", command=process_clipboard_image)
    process_button.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
