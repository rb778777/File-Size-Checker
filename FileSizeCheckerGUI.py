import os
import re
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from tqdm import tqdm
import subprocess
import webbrowser
import platform
import ctypes
from PIL import Image, ImageTk  # Add PIL import for image handling
import sys

# Function to open file or folder
def open_file_or_folder(path):
    path = os.path.normpath(path)
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":  # macOS
        subprocess.call(["open", path])
    else:  # Linux
        subprocess.call(["xdg-open", path])

class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        self.update_text_widget()

    def update_text_widget(self):
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.insert(tk.END, self.buffer)
        self.text_widget.see(tk.END)
        self.text_widget.config(state=tk.DISABLED)
        self.buffer = ""

    def flush(self):
        pass

class FileSizeCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Size Checker")
        self.root.geometry("1000x700")
        self.root.minsize(900, 650)
        
        # Try to set DPI awareness for better Windows display
        try:
            if platform.system() == "Windows":
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # Set application icon
        try:
            # Get the correct path for the icon file whether running as script or executable
            if getattr(sys, 'frozen', False):
                # If the application is running as a bundled executable
                # PyInstaller creates a temp folder and stores the path in _MEIPASS
                base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            else:
                # If running as a normal Python script
                base_path = os.path.dirname(os.path.abspath(__file__))
                
            icon_path = os.path.join(base_path, "file_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            # Fail silently if icon cannot be loaded
            print(f"Could not load icon: {e}")
        
        # Set modern theme
        self.set_modern_theme()
        
        self.scanning = False
        self.scan_thread = None
        self.results = []
        self.large_folders = []
        self.large_files = []
        
        self.create_widgets()
        
    def set_modern_theme(self):
        # Modern Windows 10/11 colors
        self.bg_color = "#202020"  # Background
        self.fg_color = "#e0e0e0"  # Text color
        self.accent_color = "#0078d7"  # Windows accent blue
        self.secondary_color = "#2d2d2d"  # Card/control background
        self.highlight_color = "#3e3e3e"  # Hover highlight
        self.success_color = "#10893e"  # Green
        self.warning_color = "#f7630c"  # Orange
        self.error_color = "#e81123"  # Red
        
        # Treeview special colors
        self.tree_bg = "#252526"  # Treeview background
        self.tree_fg = "#e0e0e0"  # Treeview text color
        self.tree_selected_bg = "#0078d7"  # Selected row bg
        self.tree_selected_fg = "#ffffff"  # Selected row text
        self.tree_hover_bg = "#3e3e42"  # Row hover highlight
        
        # Configure ttk styles
        self.style = ttk.Style()
        
        # Try to use a modern theme as base
        try:
            self.style.theme_use("clam")
        except:
            pass
            
        # Configure general styles
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        self.style.configure("Header.TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 18, "bold"))
        self.style.configure("Subheader.TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 12))
        
        # Button styles - make them look like Windows 10/11 buttons
        self.style.configure("TButton", 
                           background=self.accent_color, 
                           foreground="white", 
                           font=("Segoe UI", 10),
                           padding=(10, 5),
                           borderwidth=0)
        self.style.map("TButton",
                     background=[("active", self.highlight_color), ("disabled", self.secondary_color)],
                     foreground=[("disabled", "#a0a0a0")])
        
        # Entry style
        self.style.configure("TEntry", 
                           fieldbackground=self.secondary_color, 
                           foreground=self.fg_color,
                           bordercolor=self.accent_color,
                           lightcolor=self.secondary_color,
                           darkcolor=self.secondary_color,
                           padding=5)
        
        # Combobox style
        self.style.configure("TCombobox", 
                           fieldbackground=self.secondary_color, 
                           foreground=self.fg_color,
                           background=self.accent_color,
                           arrowsize=15,
                           padding=5)
        self.style.map("TCombobox",
                     fieldbackground=[("readonly", self.secondary_color)],
                     selectbackground=[("readonly", self.accent_color)],
                     background=[("readonly", self.secondary_color)])
                     
        # Override combobox dropdown (listbox) colors
        self.root.option_add('*TCombobox*Listbox.background', self.secondary_color)
        self.root.option_add('*TCombobox*Listbox.foreground', self.fg_color)
        self.root.option_add('*TCombobox*Listbox.selectBackground', self.accent_color)
        self.root.option_add('*TCombobox*Listbox.selectForeground', "white")
        
        # Progressbar style
        self.style.configure("TProgressbar", 
                           background=self.accent_color,
                           troughcolor="#1e1e1e",
                           bordercolor=self.bg_color)
        
        # Notebook style (tabs)
        self.style.configure("TNotebook", 
                           background=self.bg_color, 
                           tabmargins=[0, 0, 0, 0],
                           borderwidth=0)
        self.style.configure("TNotebook.Tab", 
                           background=self.secondary_color,
                           foreground=self.fg_color,
                           padding=[15, 5],
                           font=("Segoe UI", 9))
        self.style.map("TNotebook.Tab",
                     background=[("selected", self.bg_color), ("active", self.highlight_color)],
                     foreground=[("selected", self.fg_color)],
                     expand=[("selected", [0, 0, 0, 0])])
        
        # Treeview style (modern Windows Explorer look)
        self.style.configure("Treeview", 
                           background=self.tree_bg,
                           foreground=self.tree_fg,
                           rowheight=25,
                           borderwidth=0,
                           font=("Segoe UI", 10),
                           fieldbackground=self.tree_bg)  # This fixes white background in some cells
        self.style.configure("Treeview.Heading", 
                           background=self.secondary_color,
                           foreground=self.fg_color,
                           relief="flat",
                           font=("Segoe UI", 10, "bold"))
        self.style.map("Treeview",
                     background=[("selected", self.tree_selected_bg)],
                     foreground=[("selected", self.tree_selected_fg)])
        
        # Fix Treeview background color when disabled
        self.style.map("Treeview", 
                     fieldbackground=[("disabled", self.tree_bg), ("!disabled", self.tree_bg)])
        
        # Scrollbar style
        self.style.configure("TScrollbar", 
                           background=self.bg_color,
                           troughcolor=self.secondary_color,
                           bordercolor=self.bg_color,
                           arrowcolor=self.fg_color,
                           arrowsize=13)
        self.style.map("TScrollbar",
                      background=[("active", self.highlight_color)],
                      arrowcolor=[("active", self.accent_color)])
        
        # Configure the root window
        self.root.configure(bg=self.bg_color)
        
        # Override the standard dialog background colors if possible
        try:
            self.root.option_add('*Dialog.msg.background', self.bg_color)
            self.root.option_add('*Dialog.msg.foreground', self.fg_color)
            self.root.option_add('*Dialog.background', self.bg_color)
            self.root.option_add('*Dialog.foreground', self.fg_color)
        except:
            pass
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header with logo and title
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        # App logo/icon 
        logo_frame = ttk.Frame(header_frame, width=40, height=40)
        logo_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        # Try to load the custom logo image
        try:
            # Look for the image in the same directory as the script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(script_dir, "app_logo.png")
            
            # Check if custom logo exists
            if os.path.exists(logo_path):
                # Load and resize the image
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((32, 32), Image.LANCZOS)
                self.logo_img_tk = ImageTk.PhotoImage(logo_img)
                
                # Create a label to display the image
                logo_label = ttk.Label(logo_frame, image=self.logo_img_tk, background=self.bg_color)
                logo_label.pack(fill=tk.BOTH, expand=True)
            else:
                # Fallback to drawing a stylized folder icon
                logo_canvas = tk.Canvas(logo_frame, width=40, height=40, bg=self.bg_color, 
                                      highlightthickness=0)
                logo_canvas.pack(fill=tk.BOTH, expand=True)
                logo_canvas.create_rectangle(10, 15, 30, 35, fill=self.accent_color, outline="")
                logo_canvas.create_rectangle(15, 10, 35, 15, fill=self.accent_color, outline="")
        except Exception as e:
            # Fallback in case of any error
            logo_canvas = tk.Canvas(logo_frame, width=40, height=40, bg=self.bg_color, 
                                   highlightthickness=0)
            logo_canvas.pack(fill=tk.BOTH, expand=True)
            logo_canvas.create_rectangle(10, 15, 30, 35, fill=self.accent_color, outline="")
            logo_canvas.create_rectangle(15, 10, 35, 15, fill=self.accent_color, outline="")
        
        header_label = ttk.Label(header_frame, text="File Size Checker", style="Header.TLabel")
        header_label.pack(side=tk.LEFT)
        
        # Control panel frame
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Left side - Directory selection & size threshold
        left_panel = ttk.Frame(control_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Directory selection
        dir_label = ttk.Label(left_panel, text="Directory to scan:", style="Subheader.TLabel")
        dir_label.pack(anchor=tk.W, pady=(0, 5))
        
        dir_frame = ttk.Frame(left_panel)
        dir_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.dir_var = tk.StringVar(value=os.getcwd())
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var, width=60)
        self.dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        browse_btn = ttk.Button(dir_frame, text="Browse...", command=self.browse_directory)
        browse_btn.pack(side=tk.RIGHT)
        
        # Size threshold
        threshold_label = ttk.Label(left_panel, text="Size threshold:", style="Subheader.TLabel")
        threshold_label.pack(anchor=tk.W, pady=(0, 5))
        
        size_frame = ttk.Frame(left_panel)
        size_frame.pack(fill=tk.X)
        
        self.size_var = tk.StringVar(value="1")
        size_entry = ttk.Entry(size_frame, textvariable=self.size_var, width=10)
        size_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        self.unit_var = tk.StringVar(value="GB")
        unit_combo = ttk.Combobox(size_frame, textvariable=self.unit_var, 
                                 values=["B", "KB", "MB", "GB", "TB"], 
                                 width=5, state="readonly")
        unit_combo.pack(side=tk.LEFT)
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.scan_btn = ttk.Button(btn_frame, text="Start Scan", command=self.start_scan, width=15)
        self.scan_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = ttk.Button(btn_frame, text="Stop Scan", command=self.stop_scan, state=tk.DISABLED, width=15)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.export_btn = ttk.Button(btn_frame, text="Export Results", command=self.export_results, state=tk.DISABLED, width=15)
        self.export_btn.pack(side=tk.LEFT)
        
        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.progress_bar = ttk.Progressbar(progress_frame, orient=tk.HORIZONTAL, mode="indeterminate", length=100)
        self.progress_bar.pack(fill=tk.X)
        
        # Summary frame
        self.summary_frame = ttk.Frame(main_frame)
        self.summary_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Results notebook (tabbed interface)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Stats tab
        self.stats_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.stats_frame, text="Statistics")
        
        # Folders tab with treeview
        self.folders_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.folders_frame, text="Large Folders")
        
        # Setup folders treeview
        folders_container = ttk.Frame(self.folders_frame, style="TFrame")
        folders_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Add a column header frame
        folders_header_frame = ttk.Frame(folders_container, style="TFrame")
        folders_header_frame.pack(fill=tk.X)
        
        # Path header (left column)
        path_header = ttk.Label(folders_header_frame, text="Path", font=("Segoe UI", 10, "bold"), 
                              background=self.secondary_color, foreground=self.fg_color, anchor=tk.W, padding=5)
        path_header.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Size header (right column)
        size_header = ttk.Label(folders_header_frame, text="Size", font=("Segoe UI", 10, "bold"), 
                              background=self.secondary_color, foreground=self.fg_color, 
                              width=12, anchor=tk.E, padding=5)
        size_header.pack(side=tk.RIGHT)
        
        # Container for treeview and scrollbar
        folders_view_frame = ttk.Frame(folders_container, style="TFrame")
        folders_view_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create folders treeview
        self.folders_tree = ttk.Treeview(folders_view_frame, columns=("size"), show="tree", 
                                       style="Treeview", selectmode="browse")
        self.folders_tree.column("#0", width=700, stretch=True)
        self.folders_tree.column("size", width=100, anchor=tk.E, stretch=False)
        
        # Create scrollbars
        folders_vsb = ttk.Scrollbar(folders_view_frame, orient="vertical", command=self.folders_tree.yview)
        folders_hsb = ttk.Scrollbar(folders_container, orient="horizontal", command=self.folders_tree.xview)
        self.folders_tree.configure(yscrollcommand=folders_vsb.set, xscrollcommand=folders_hsb.set)
        
        # Pack scrollbars and treeview
        folders_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.folders_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        folders_hsb.pack(fill=tk.X)
        
        # Add double-click event to open folder
        self.folders_tree.bind("<Double-1>", self.on_folder_double_click)
        
        # Files tab with treeview
        self.files_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.files_frame, text="Large Files")
        
        # Similar container setup for files
        files_container = ttk.Frame(self.files_frame, style="TFrame")
        files_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Add a column header frame
        files_header_frame = ttk.Frame(files_container, style="TFrame")
        files_header_frame.pack(fill=tk.X)
        
        # Path header (left column)
        file_path_header = ttk.Label(files_header_frame, text="File Path", font=("Segoe UI", 10, "bold"), 
                                   background=self.secondary_color, foreground=self.fg_color, anchor=tk.W, padding=5)
        file_path_header.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Size header (right column)
        file_size_header = ttk.Label(files_header_frame, text="Size", font=("Segoe UI", 10, "bold"), 
                                   background=self.secondary_color, foreground=self.fg_color, 
                                   width=12, anchor=tk.E, padding=5)
        file_size_header.pack(side=tk.RIGHT)
        
        # Container for treeview and scrollbar
        files_view_frame = ttk.Frame(files_container, style="TFrame")
        files_view_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create files treeview
        self.files_tree = ttk.Treeview(files_view_frame, columns=("size"), show="tree", 
                                     style="Treeview", selectmode="browse")
        self.files_tree.column("#0", width=700, stretch=True)
        self.files_tree.column("size", width=100, anchor=tk.E, stretch=False)
        
        # Create scrollbars
        files_vsb = ttk.Scrollbar(files_view_frame, orient="vertical", command=self.files_tree.yview)
        files_hsb = ttk.Scrollbar(files_container, orient="horizontal", command=self.files_tree.xview)
        self.files_tree.configure(yscrollcommand=files_vsb.set, xscrollcommand=files_hsb.set)
        
        # Pack scrollbars and treeview
        files_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        files_hsb.pack(fill=tk.X)
        
        # Add double-click event to open file
        self.files_tree.bind("<Double-1>", self.on_file_double_click)
        
        # Errors tab
        self.errors_frame = ttk.Frame(self.notebook, style="TFrame")
        self.notebook.add(self.errors_frame, text="Errors")
        
        # Setup errors list with modern styling
        errors_container = ttk.Frame(self.errors_frame, style="TFrame")
        errors_container.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        # Use a Treeview for errors as well for consistent styling
        self.errors_tree = ttk.Treeview(errors_container, columns=("error"), show="tree", 
                                      style="Treeview", selectmode="browse")
        self.errors_tree.column("#0", width=300, stretch=True)
        self.errors_tree.column("error", width=500, stretch=True)
        
        # Create scrollbars
        errors_vsb = ttk.Scrollbar(errors_container, orient="vertical", command=self.errors_tree.yview)
        errors_hsb = ttk.Scrollbar(errors_container, orient="horizontal", command=self.errors_tree.xview)
        self.errors_tree.configure(yscrollcommand=errors_vsb.set, xscrollcommand=errors_hsb.set)
        
        # Pack scrollbars and treeview
        errors_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.errors_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        errors_hsb.pack(fill=tk.X)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.FLAT, 
                             background=self.secondary_color, anchor=tk.W, padding=(5, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def on_folder_double_click(self, event):
        selected_items = self.folders_tree.selection()
        if not selected_items:
            return
            
        item_id = selected_items[0]
        folder_path = self.folders_tree.item(item_id, "text")
        
        # Highlight momentarily
        self.folders_tree.item(item_id, tags=("highlight",))
        self.folders_tree.tag_configure("highlight", background=self.accent_color)
        self.root.after(300, lambda: self.folders_tree.item(item_id, tags=()))
        
        try:
            open_file_or_folder(folder_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
    
    def on_file_double_click(self, event):
        selected_items = self.files_tree.selection()
        if not selected_items:
            return
            
        item_id = selected_items[0]
        file_path = self.files_tree.item(item_id, "text")
        
        # Highlight momentarily
        self.files_tree.item(item_id, tags=("highlight",))
        self.files_tree.tag_configure("highlight", background=self.accent_color)
        self.root.after(300, lambda: self.files_tree.item(item_id, tags=()))
        
        try:
            # Get absolute normalized path
            file_path = os.path.abspath(os.path.normpath(file_path))
            
            # On Windows, open Explorer and select the file
            if platform.system() == "Windows":
                # For Windows, the correct command is: explorer /select,"exact path with quotes"
                # Use shell=True for complex commands with arguments containing commas
                subprocess.Popen(f'explorer /select,"{file_path}"', shell=True)
            else:
                # On other platforms, just open the containing folder
                dir_path = os.path.dirname(file_path)
                open_file_or_folder(dir_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file location: {e}")
    
    def browse_directory(self):
        dir_path = filedialog.askdirectory(initialdir=self.dir_var.get())
        if dir_path:
            self.dir_var.set(dir_path)
    
    def start_scan(self):
        # Validate inputs
        dir_path = self.dir_var.get()
        if not os.path.isdir(dir_path):
            messagebox.showerror("Error", "Invalid directory path!")
            return
        
        try:
            size_value = float(self.size_var.get())
            if size_value <= 0:
                raise ValueError("Size must be positive")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number for the size threshold!")
            return
        
        # Prepare UI
        self.clear_results()
        
        self.scan_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        
        self.progress_bar.start()
        self.status_var.set("Scanning...")
        self.scanning = True
        
        # Convert size to bytes
        unit = self.unit_var.get()
        unit_multipliers = {
            "B": 1,
            "KB": 1024,
            "MB": 1024 ** 2,
            "GB": 1024 ** 3,
            "TB": 1024 ** 4
        }
        size_threshold = size_value * unit_multipliers[unit]
        
        # Start scan in a separate thread
        self.scan_thread = threading.Thread(
            target=self.run_scan, 
            args=(dir_path, size_threshold),
            daemon=True
        )
        self.scan_thread.start()
    
    def clear_results(self):
        # Clear statistics
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
            
        # Clear folders tree
        for item in self.folders_tree.get_children():
            self.folders_tree.delete(item)
            
        # Clear files tree
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
            
        # Clear errors tree
        for item in self.errors_tree.get_children():
            self.errors_tree.delete(item)
    
    def run_scan(self, dir_path, size_threshold):
        try:
            scan_results = self.get_scan_results(dir_path, size_threshold)
            
            # Update UI with results
            self.root.after(0, lambda: self.display_results(scan_results))
                
            # Update UI
            self.root.after(0, self.scan_completed)
        except Exception as e:
            self.root.after(0, lambda: self.display_error(str(e)))
            self.root.after(0, self.scan_failed, str(e))
    
    def display_error(self, error_msg):
        # Clear statistics and add error message
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
            
        error_label = ttk.Label(self.stats_frame, 
                              text=f"Scan failed: {error_msg}",
                              foreground=self.error_color)
        error_label.pack(pady=20)
    
    def display_results(self, scan_results):
        total_size, scan_time, folder_count, file_count, self.large_folders, self.large_files, error_paths = scan_results
        
        # Clear existing widgets in stats_frame
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
            
        # Display statistics
        stats_canvas = tk.Canvas(self.stats_frame, bg=self.bg_color, highlightthickness=0)
        stats_canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create card-like frames for stats
        card_width = 220
        card_height = 130
        card_margin = 20
        
        # Total storage card
        storage_card = tk.Frame(stats_canvas, bg=self.secondary_color, bd=0, highlightthickness=0)
        stats_canvas.create_window(card_margin, card_margin, 
                                 anchor=tk.NW, window=storage_card, 
                                 width=card_width, height=card_height)
        
        # Add a bit of padding
        inner_pad = tk.Frame(storage_card, bg=self.secondary_color)
        inner_pad.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(inner_pad, text="Total Storage", 
               bg=self.secondary_color, fg=self.fg_color, 
               font=("Segoe UI", 12)).pack(anchor=tk.W)
        
        tk.Label(inner_pad, text=self.format_size(total_size), 
               bg=self.secondary_color, fg=self.accent_color, 
               font=("Segoe UI", 18, "bold")).pack(anchor=tk.W, pady=(10, 0))
        
        # Folders card
        folders_card = tk.Frame(stats_canvas, bg=self.secondary_color, bd=0, highlightthickness=0)
        stats_canvas.create_window(card_margin*2 + card_width, card_margin, 
                                 anchor=tk.NW, window=folders_card, 
                                 width=card_width, height=card_height)
        
        # Add a bit of padding
        inner_pad = tk.Frame(folders_card, bg=self.secondary_color)
        inner_pad.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(inner_pad, text="Folders", 
               bg=self.secondary_color, fg=self.fg_color, 
               font=("Segoe UI", 12)).pack(anchor=tk.W)
        
        tk.Label(inner_pad, text=str(folder_count), 
               bg=self.secondary_color, fg=self.accent_color, 
               font=("Segoe UI", 18, "bold")).pack(anchor=tk.W, pady=(5, 0))
        
        tk.Label(inner_pad, text=f"{len(self.large_folders)} large", 
               bg=self.secondary_color, fg=self.fg_color).pack(anchor=tk.W, pady=(5, 0))
        
        # Files card
        files_card = tk.Frame(stats_canvas, bg=self.secondary_color, bd=0, highlightthickness=0)
        stats_canvas.create_window(card_margin*3 + card_width*2, card_margin, 
                                 anchor=tk.NW, window=files_card, 
                                 width=card_width, height=card_height)
        
        # Add a bit of padding
        inner_pad = tk.Frame(files_card, bg=self.secondary_color)
        inner_pad.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(inner_pad, text="Files", 
               bg=self.secondary_color, fg=self.fg_color, 
               font=("Segoe UI", 12)).pack(anchor=tk.W)
        
        tk.Label(inner_pad, text=str(file_count), 
               bg=self.secondary_color, fg=self.accent_color, 
               font=("Segoe UI", 18, "bold")).pack(anchor=tk.W, pady=(5, 0))
        
        tk.Label(inner_pad, text=f"{len(self.large_files)} large", 
               bg=self.secondary_color, fg=self.fg_color).pack(anchor=tk.W, pady=(5, 0))
        
        # Scan time card
        time_card = tk.Frame(stats_canvas, bg=self.secondary_color, bd=0, highlightthickness=0)
        stats_canvas.create_window(card_margin, card_margin*2 + card_height, 
                                 anchor=tk.NW, window=time_card, 
                                 width=card_width, height=card_height)
        
        # Add a bit of padding
        inner_pad = tk.Frame(time_card, bg=self.secondary_color)
        inner_pad.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        tk.Label(inner_pad, text="Scan Time", 
               bg=self.secondary_color, fg=self.fg_color, 
               font=("Segoe UI", 12)).pack(anchor=tk.W)
        
        tk.Label(inner_pad, text=f"{scan_time:.2f} sec", 
               bg=self.secondary_color, fg=self.accent_color, 
               font=("Segoe UI", 18, "bold")).pack(anchor=tk.W, pady=(10, 0))
        
        # Update folders tree
        row_count = 0
        for folder, size in self.large_folders:
            item_id = self.folders_tree.insert("", "end", text=folder, values=(self.format_size(size),))
            
            # Add appropriate tag for alternating rows and coloring by size
            tags = []
            if row_count % 2 == 1:
                tags.append("odd_row")
                
            if size > 10 * 1024**3:  # > 10GB
                tags.append("very_large")
            elif size > 5 * 1024**3:  # > 5GB
                tags.append("large")
            else:
                tags.append("medium")
                
            self.folders_tree.item(item_id, tags=tags)
            row_count += 1
        
        # Configure tree tags
        self.folders_tree.tag_configure("odd_row", background="#2a2a2a")  # Alternating row color
        self.folders_tree.tag_configure("very_large", foreground=self.error_color)
        self.folders_tree.tag_configure("large", foreground=self.warning_color)
        self.folders_tree.tag_configure("medium", foreground=self.success_color)
        
        # Update files tree
        row_count = 0
        for file, size in self.large_files:
            # Get just the filename for display
            file_name = os.path.basename(file)
            # Use the file path as the item text for opening on double-click
            item_id = self.files_tree.insert("", "end", text=file, values=(self.format_size(size),))
            
            # Add appropriate tag for alternating rows and coloring by size
            tags = []
            if row_count % 2 == 1:
                tags.append("odd_row")
                
            if size > 1 * 1024**3:  # > 1GB
                tags.append("very_large")
            elif size > 500 * 1024**2:  # > 500MB
                tags.append("large")
            else:
                tags.append("medium")
                
            self.files_tree.item(item_id, tags=tags)
            row_count += 1
        
        # Configure tree tags
        self.files_tree.tag_configure("odd_row", background="#2a2a2a")  # Alternating row color
        self.files_tree.tag_configure("very_large", foreground=self.error_color)
        self.files_tree.tag_configure("large", foreground=self.warning_color)
        self.files_tree.tag_configure("medium", foreground=self.success_color)
        
        # Update errors tree
        row_count = 0
        for path, error in error_paths:
            item_id = self.errors_tree.insert("", "end", text=path, values=(error,))
            
            # Add alternating row tag
            if row_count % 2 == 1:
                self.errors_tree.item(item_id, tags=("odd_row",))
            row_count += 1
            
        # Configure error tree tags
        self.errors_tree.tag_configure("odd_row", background="#2a2a2a")  # Alternating row color
        
        # Update tab text to show counts
        self.notebook.tab(1, text=f"Large Folders ({len(self.large_folders)})")
        self.notebook.tab(2, text=f"Large Files ({len(self.large_files)})")
        self.notebook.tab(3, text=f"Errors ({len(error_paths)})")
        
        # Switch to the appropriate tab based on results
        if len(self.large_files) > 0:
            self.notebook.select(2)  # Files tab
        elif len(self.large_folders) > 0:
            self.notebook.select(1)  # Folders tab
    
    def get_scan_results(self, start_path, size_threshold):
        total_size = 0
        folder_sizes = {}
        file_count = 0
        folder_count = 0
        large_folders = []
        large_files = []
        error_paths = []
        
        # Update status
        self.root.after(0, lambda: self.progress_label.config(text="Counting files and folders..."))
        
        # First pass - count files and folders
        try:
            for dirpath, dirnames, filenames in os.walk(start_path):
                if not self.scanning:  # Check if scan was cancelled
                    return (0, 0, 0, 0, [], [], ["Scan cancelled"])
                    
                folder_count += 1
                file_count += len(filenames)
                
                # Update count every 100 folders
                if folder_count % 100 == 0:
                    self.root.after(0, lambda c=folder_count, f=file_count: 
                        self.progress_label.config(text=f"Counting: {c:,} folders, {f:,} files found..."))
        except PermissionError:
            error_paths.append((start_path, "Permission denied when accessing some directories. Results may be incomplete."))
        
        if not self.scanning:  # Check if scan was cancelled
            return (0, 0, 0, 0, [], [], ["Scan cancelled"])
            
        # Set up tracking variables
        start_time = time.time()
        items_processed = 0
        total_items = folder_count + file_count
        
        self.root.after(0, lambda: self.progress_label.config(
            text=f"Scanning {folder_count:,} folders and {file_count:,} files..."))
        self.root.after(0, lambda: self.progress_bar.config(mode="determinate", maximum=total_items, value=0))
        
        # Second pass - analyze sizes
        for dirpath, dirnames, filenames in os.walk(start_path):
            if not self.scanning:  # Check if scan was cancelled
                return (0, 0, 0, 0, [], [], ["Scan cancelled"])
                
            folder_size = 0
            
            for f in filenames:
                if not self.scanning:  # Check if scan was cancelled
                    return (0, 0, 0, 0, [], [], ["Scan cancelled"])
                    
                fp = os.path.join(dirpath, f)
                try:
                    if os.path.isfile(fp):
                        try:
                            file_size = os.path.getsize(fp)
                            total_size += file_size
                            folder_size += file_size
                            
                            if file_size > size_threshold:
                                large_files.append((fp, file_size))
                        except (OSError, FileNotFoundError):
                            # Handle files that disappeared during scan
                            pass
                except (PermissionError, OSError) as e:
                    error_paths.append((fp, str(e)))
                
                # Update progress
                items_processed += 1
                if items_processed % 50 == 0:
                    self.root.after(0, lambda p=items_processed: self.update_progress(p, total_items))
            
            folder_sizes[dirpath] = folder_size
            
            if folder_size > size_threshold:
                large_folders.append((dirpath, folder_size))
            
            # Update progress for the folder
            items_processed += 1
            if items_processed % 50 == 0:
                self.root.after(0, lambda p=items_processed: self.update_progress(p, total_items))
        
        # Finalize results
        scan_time = time.time() - start_time
        
        # Sort large folders and files by size (largest first)
        large_folders.sort(key=lambda x: x[1], reverse=True)
        large_files.sort(key=lambda x: x[1], reverse=True)
        
        return (total_size, scan_time, folder_count, file_count, large_folders, large_files, error_paths)
    
    def update_progress(self, current, total):
        self.progress_bar.config(value=current)
        percent = int(current / total * 100) if total > 0 else 0
        self.progress_label.config(text=f"Scanning... {percent}% ({current:,}/{total:,})")
        self.status_var.set(f"Scanning: {percent}% complete")
    
    def scan_completed(self):
        self.progress_bar.stop()
        self.progress_bar.config(value=100)
        self.progress_label.config(text="Scan completed")
        self.status_var.set("Ready")
        
        self.scan_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.NORMAL)
        
        self.scanning = False
    
    def scan_failed(self, error_msg):
        self.progress_bar.stop()
        self.progress_label.config(text="Scan failed")
        self.status_var.set(f"Error: {error_msg}")
        
        self.scan_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        
        self.scanning = False
        messagebox.showerror("Scan Failed", f"The scan failed with error:\n{error_msg}")
    
    def stop_scan(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to stop the current scan?"):
            self.scanning = False
            self.status_var.set("Cancelling scan...")
            self.progress_label.config(text="Cancelling...")
    
    def export_results(self):
        if not hasattr(self, 'large_folders') and not hasattr(self, 'large_files'):
            messagebox.showinfo("No Results", "No results to export.")
            return
        
        export_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("CSV files", "*.csv"), ("HTML files", "*.html"), ("All files", "*.*")],
            initialfile=f"file_size_results_{time.strftime('%Y%m%d-%H%M%S')}"
        )
        
        if not export_path:
            return  # User cancelled
        
        try:
            # Export based on file extension
            if export_path.lower().endswith('.csv'):
                self.export_as_csv(export_path)
            elif export_path.lower().endswith('.html'):
                self.export_as_html(export_path)
            else:  # Default to text
                self.export_as_text(export_path)
            
            # Ask if user wants to open the exported file
            if messagebox.askyesno("Export Successful", f"Results exported to:\n{export_path}\n\nDo you want to open the file?"):
                open_file_or_folder(export_path)
                
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export results: {str(e)}")
    
    def export_as_text(self, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"File Size Check Results - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Directory: {os.path.abspath(self.dir_var.get())}\n")
            f.write(f"Size threshold: {self.size_var.get()} {self.unit_var.get()}\n\n")
            
            # Write folders
            f.write(f"Large Folders ({len(self.large_folders)}):\n")
            f.write("-" * 80 + "\n")
            for folder, size in self.large_folders:
                f.write(f"{folder} | {self.format_size(size)}\n")
            
            # Write files
            f.write(f"\nLarge Files ({len(self.large_files)}):\n")
            f.write("-" * 80 + "\n")
            for file, size in self.large_files:
                f.write(f"{file} | {self.format_size(size)}\n")
    
    def export_as_csv(self, filepath):
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            import csv
            writer = csv.writer(f)
            
            # Write header and metadata
            writer.writerow(["File Size Check Results", time.strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(["Directory", os.path.abspath(self.dir_var.get())])
            writer.writerow(["Size threshold", f"{self.size_var.get()} {self.unit_var.get()}"])
            writer.writerow([])
            
            # Write folders section
            writer.writerow([f"Large Folders ({len(self.large_folders)}):"])
            writer.writerow(["Path", "Size"])
            for folder, size in self.large_folders:
                writer.writerow([folder, self.format_size(size)])
            
            writer.writerow([])
            
            # Write files section
            writer.writerow([f"Large Files ({len(self.large_files)}):"])
            writer.writerow(["Path", "Size"])
            for file, size in self.large_files:
                writer.writerow([file, self.format_size(size)])
    
    def export_as_html(self, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            # Write HTML header
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>File Size Check Results</title>
    <style>
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 20px; 
            background-color: #202020;
            color: #e0e0e0;
        }}
        h1, h2 {{ color: #0078d7; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .metadata {{ 
            background-color: #2d2d2d;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }}
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            margin-bottom: 30px;
            background-color: #252526;
        }}
        th {{ 
            background-color: #0078d7; 
            color: white; 
            text-align: left; 
            padding: 10px; 
        }}
        td {{ 
            padding: 8px 10px; 
            border-bottom: 1px solid #3e3e3e; 
        }}
        tr:nth-child(even) {{ background-color: #2a2a2a; }}
        tr:hover {{ background-color: #3e3e42; }}
        .size-very-large {{ color: #e81123; }}
        .size-large {{ color: #f7630c; }}
        .size-medium {{ color: #10893e; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>File Size Check Results</h1>
        <div class="metadata">
            <p><strong>Date:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Directory:</strong> {os.path.abspath(self.dir_var.get())}</p>
            <p><strong>Size threshold:</strong> {self.size_var.get()} {self.unit_var.get()}</p>
        </div>
""")
            
            # Write folders section
            f.write(f"""        <h2>Large Folders ({len(self.large_folders)})</h2>
        <table>
            <tr>
                <th>Path</th>
                <th>Size</th>
            </tr>
""")
            for folder, size in self.large_folders:
                size_class = "size-very-large" if size > 10 * 1024**3 else "size-large" if size > 5 * 1024**3 else "size-medium"
                f.write(f"""            <tr>
                <td>{folder}</td>
                <td class="{size_class}">{self.format_size(size)}</td>
            </tr>
""")
            f.write("        </table>\n")
            
            # Write files section
            f.write(f"""        <h2>Large Files ({len(self.large_files)})</h2>
        <table>
            <tr>
                <th>Path</th>
                <th>Size</th>
            </tr>
""")
            for file, size in self.large_files:
                size_class = "size-very-large" if size > 1 * 1024**3 else "size-large" if size > 500 * 1024**2 else "size-medium"
                f.write(f"""            <tr>
                <td>{file}</td>
                <td class="{size_class}">{self.format_size(size)}</td>
            </tr>
""")
            f.write("        </table>\n")
            
            # Close HTML
            f.write("""    </div>
</body>
</html>""")
    
    def format_size(self, size_bytes):
        """Format the size in bytes to a human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0 or unit == 'TB':
                break
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} {unit}"

if __name__ == "__main__":
    # Enable DPI awareness for better display on Windows
    try:
        if platform.system() == "Windows":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
            
            # Force Windows to use dark mode for system dialogs (Windows 10 1809+)
            try:
                windll.dwmapi.DwmSetWindowAttribute(
                    None, 
                    20,  # DWMWA_USE_IMMERSIVE_DARK_MODE
                    ctypes.byref(ctypes.c_int(1)), 
                    ctypes.sizeof(ctypes.c_int)
                )
            except:
                pass
    except:
        pass
        
    root = tk.Tk()
    app = FileSizeCheckerApp(root)
    root.mainloop() 