import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import zipfile
import json
import shutil

class TiruguViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Tirugu - 360 Product Image Viewer")
        self.geometry("1920x1080")
        self.iconphoto(False, ImageTk.PhotoImage(file='Tirugu.jpg'))
        
        # Bind the configure event to resize the image when the window is resized
        self.bind("<Configure>", self.on_window_resize)

        # Create a Notebook widget to manage multiple tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True)

        self.images = {}
        self.current_image_index = {}
        self.is_spinning = {}
        self.mouse_dragging = {}
        self.last_mouse_x = {}
        self.last_mouse_y = {}
        self.zoom_scale = {}
        self.image_offset_x = {}
        self.image_offset_y = {}
        self.canvas_images = {}

        # Create the menu bar
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Image Sequence", command=self.open_image_sequence)
        file_menu.add_command(label="Open .tirf File", command=self.open_tirf_file)
        file_menu.add_command(label="Save as .tirf", command=self.save_as_tirf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

        # Store the canvas size
        self.canvas_width = 1920
        self.canvas_height = 1080

    def on_window_resize(self, event):
        """Adjust the canvas size and image display on window resize."""
        if event.widget == self:
            self.canvas_width = event.width
            self.canvas_height = event.height
            for tab_name in self.images:
                if self.images[tab_name]:
                    # Update the image display for each tab
                    self.display_image(self.images[tab_name][self.current_image_index[tab_name]], self.notebook.nametowidget(self.notebook.select()))

    def display_image(self, image, tab_frame):
        """Display the image on the tab frame's canvas, resizing it with the zoom scale."""
        tab_name = self.notebook.tab(self.notebook.select(), "text")
        image_width, image_height = image.size
        scale = self.zoom_scale[tab_name]
        new_width = int(image_width * scale)
        new_height = int(image_height * scale)

        # Resize the image to the new dimensions
        resized_image = image.resize((new_width, new_height), Image.LANCZOS)
        tk_image = ImageTk.PhotoImage(resized_image)

        # Update the canvas size and display the image centered
        canvas = tab_frame.winfo_children()[0]
        self.canvas_images[tab_name] = tk_image
        canvas.delete("all")  # Clear the canvas before drawing the new image
        canvas.create_image(self.image_offset_x[tab_name], self.image_offset_y[tab_name], anchor="nw", image=self.canvas_images[tab_name])
        canvas.image = tk_image

    def open_image_sequence(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return

        # Use the folder name as the exact tab name
        tab_name = os.path.basename(folder_path)
        tab_frame = self.create_new_tab(tab_name)

        images = []
        for file_name in sorted(os.listdir(folder_path)):
            if file_name.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                img_path = os.path.join(folder_path, file_name)
                try:
                    image = Image.open(img_path)
                    images.append(image)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to load image {file_name}: {e}")

        if images:
            self.images[tab_name] = images
            self.display_image(images[0], tab_frame)
            self.after(100, self.spin_images, tab_name, tab_frame)  # Adjusted rotation speed

    def save_as_tirf(self):
        current_tab = self.notebook.select()
        if not current_tab:
            messagebox.showerror("Error", "No tab selected")
            return

        tab_name = self.notebook.tab(current_tab, "text")

        if tab_name not in self.images or not self.images[tab_name]:
            messagebox.showerror("Error", "No images loaded to save as .tirf")
            return

        file_path = filedialog.asksaveasfilename(defaultextension=".tirf", filetypes=[("Tirige File", "*.tirf")])
        if not file_path:
            return

        temp_dir = f"temp_{tab_name}"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        metadata = []
        try:
            with zipfile.ZipFile(file_path, 'w') as zipf:
                for idx, image in enumerate(self.images[tab_name]):
                    if image.mode == "RGBA":
                        image = image.convert("RGB")
                    file_name = f"image_{idx + 1}.jpg"
                    image_path = os.path.join(temp_dir, file_name)
                    image.save(image_path, format="JPEG")
                    zipf.write(image_path, file_name)
                    metadata.append({"file_name": file_name, "size": image.size, "mode": "RGB"})

                metadata_path = os.path.join(temp_dir, "metadata.json")
                with open(metadata_path, 'w') as meta_file:
                    json.dump(metadata, meta_file)
                zipf.write(metadata_path, "metadata.json")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save .tirf file: {e}")
            shutil.rmtree(temp_dir)
            return

        shutil.rmtree(temp_dir)
        messagebox.showinfo("Success", f"Saved as .tirf file: {file_path}")

    def open_tirf_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Tirige Files", "*.tirf")])
        if not file_path:
            return

        tab_name = os.path.basename(file_path)
        tab_frame = self.create_new_tab(tab_name)

        temp_extract_dir = f"temp_extracted_{tab_name}"
        if os.path.exists(temp_extract_dir):
            shutil.rmtree(temp_extract_dir)
        os.makedirs(temp_extract_dir)

        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(temp_extract_dir)
            with open(os.path.join(temp_extract_dir, "metadata.json"), 'r') as meta_file:
                metadata = json.load(meta_file)
                images = []
                for data in metadata:
                    img_path = os.path.join(temp_extract_dir, data['file_name'])
                    try:
                        image = Image.open(img_path)
                        images.append(image)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to load image {data['file_name']}: {e}")

        if images:
            self.images[tab_name] = images
            self.display_image(images[0], tab_frame)
            self.after(300, self.spin_images, tab_name, tab_frame)  # Adjusted rotation speed

    def create_new_tab(self, tab_name):
        tab_frame = tk.Frame(self.notebook)
        self.notebook.add(tab_frame, text=tab_name)

        self.notebook.bind("<Button-3>", self.close_tab)

        self.images[tab_name] = []
        self.current_image_index[tab_name] = 0
        self.is_spinning[tab_name] = True
        self.mouse_dragging[tab_name] = False
        self.last_mouse_x[tab_name] = 0
        self.last_mouse_y[tab_name] = 0
        self.zoom_scale[tab_name] = 1.0
        self.image_offset_x[tab_name] = 0
        self.image_offset_y[tab_name] = 0

        canvas = tk.Canvas(tab_frame, width=self.canvas_width, height=self.canvas_height, relief=tk.SUNKEN)
        canvas.config(highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.bind("<MouseWheel>", lambda event: self.on_mouse_wheel(tab_name, event))
        canvas.bind("<ButtonPress-1>", lambda event: self.on_mouse_press(tab_name, event))
        canvas.bind("<B1-Motion>", lambda event: self.on_mouse_drag(tab_name, event))
        canvas.bind("<ButtonRelease-1>", lambda event: self.on_mouse_release(tab_name, event))
        canvas.bind("<ButtonPress-2>", lambda event: self.on_middle_mouse_press(tab_name, event))
        canvas.bind("<B2-Motion>", lambda event: self.on_middle_mouse_drag(tab_name, event))
        canvas.bind("<ButtonRelease-2>", lambda event: self.on_middle_mouse_release(tab_name, event))

        return tab_frame

    def close_tab(self, event):
        try:
            tab_id = self.notebook.index("@%d,%d" % (event.x, event.y))
            if tab_id >= 0:
                tab_name = self.notebook.tab(tab_id, "text")
                self.is_spinning[tab_name] = False  # Stop spinning when the tab is closed
                self.notebook.forget(tab_id)
        except tk.TclError:
            pass

    def spin_images(self, tab_name, tab_frame):
        if self.is_spinning.get(tab_name, False):
            self.current_image_index[tab_name] = (self.current_image_index[tab_name] + 1) % len(self.images[tab_name])
            self.display_image(self.images[tab_name][self.current_image_index[tab_name]], tab_frame)
        self.after(800, self.spin_images, tab_name, tab_frame)  # Slightly faster rotation speed for smoother spinning

    def toggle_spin(self, tab_name):
        self.is_spinning[tab_name] = not self.is_spinning[tab_name]

    def previous_image(self, tab_name, tab_frame):
        self.is_spinning[tab_name] = False
        self.current_image_index[tab_name] = (self.current_image_index[tab_name] - 1) % len(self.images[tab_name])
        self.display_image(self.images[tab_name][self.current_image_index[tab_name]], tab_frame)
        self.is_spinning[tab_name] = True  # Continue spinning after manual control

    def next_image(self, tab_name, tab_frame):
        self.is_spinning[tab_name] = False
        self.current_image_index[tab_name] = (self.current_image_index[tab_name] + 1) % len(self.images[tab_name])
        self.display_image(self.images[tab_name][self.current_image_index[tab_name]], tab_frame)
        self.is_spinning[tab_name] = True  # Continue spinning after manual control

    def adjust_zoom(self, tab_name, zoom_factor, center_x=None, center_y=None):
        self.zoom_scale[tab_name] *= zoom_factor
        if center_x is not None and center_y is not None:
            # Adjust the offsets to center the zoom around the clicked position
            self.image_offset_x[tab_name] = center_x - (center_x - self.image_offset_x[tab_name]) * zoom_factor
            self.image_offset_y[tab_name] = center_y - (center_y - self.image_offset_y[tab_name]) * zoom_factor

        # Ensure the image is correctly aligned with the canvas
        image_width, image_height = self.images[tab_name][self.current_image_index[tab_name]].size
        new_width = int(image_width * self.zoom_scale[tab_name])
        new_height = int(image_height * self.zoom_scale[tab_name])
        self.image_offset_x[tab_name] = max(min(self.image_offset_x[tab_name], self.canvas_width - new_width), 0)
        self.image_offset_y[tab_name] = max(min(self.image_offset_y[tab_name], self.canvas_height - new_height), 0)

        self.display_image(self.images[tab_name][self.current_image_index[tab_name]], self.notebook.nametowidget(self.notebook.select()))

    def on_mouse_wheel(self, tab_name, event):
        if event.delta > 0:
            self.adjust_zoom(tab_name, 1.1, event.x, event.y)
        else:
            self.adjust_zoom(tab_name, 0.9, event.x, event.y)

    def on_mouse_press(self, tab_name, event):
        self.is_spinning[tab_name] = False
        self.mouse_dragging[tab_name] = True
        self.last_mouse_x[tab_name] = event.x
        self.last_mouse_y[tab_name] = event.y

    def on_mouse_drag(self, tab_name, event):
        if self.mouse_dragging[tab_name]:
            delta_x = event.x - self.last_mouse_x[tab_name]
            if abs(delta_x) > 5:  # Increased sensitivity threshold for smoother manual rotation
                if delta_x < 0:
                    self.previous_image(tab_name, self.notebook.nametowidget(self.notebook.select()))
                else:
                    self.next_image(tab_name, self.notebook.nametowidget(self.notebook.select()))
            self.last_mouse_x[tab_name] = event.x

    def on_mouse_release(self, tab_name, event):
        self.mouse_dragging[tab_name] = False
        self.is_spinning[tab_name] = True  # Continue spinning after manual control

    def on_middle_mouse_press(self, tab_name, event):
        canvas = self.notebook.nametowidget(self.notebook.select()).winfo_children()[0]
        canvas.scan_mark(event.x, event.y)

    def on_middle_mouse_drag(self, tab_name, event):
        canvas = self.notebook.nametowidget(self.notebook.select()).winfo_children()[0]
        canvas.scan_dragto(event.x, event.y, gain=1)

    def on_middle_mouse_release(self, tab_name, event):
        pass

if __name__ == "__main__":
    app = TiruguViewer()
    app.mainloop()
