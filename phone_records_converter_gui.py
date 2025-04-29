import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
import sys
from file_converter import convert_file, batch_convert_files

# Define constants
FONT_FAMILY = 'Segoe UI'
BUTTON_STYLE_CONVERT = 'Convert.TButton'

# Define color scheme
COLORS = {
    "primary": "#3498db",  # Blue
    "secondary": "#2ecc71",  # Green
    "accent": "#e74c3c",  # Red
    "background": "#f9f9f9",  # Light gray
    "text": "#2c3e50",  # Dark blue/gray
    "success": "#27ae60",  # Dark green
    "warning": "#f39c12",  # Orange
    "error": "#c0392b"  # Dark red
}

class PhoneRecordsConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Records File Converter")
        self.root.geometry("700x650")
        self.root.configure(bg=COLORS["background"])
        
        # Set application icon if available
        try:
            self.root.iconbitmap("icon.ico")
        except Exception as e:
            # Icon not available, continue without it
            pass
        
        # Apply a theme to ttk widgets
        style = ttk.Style()
        style.theme_use('clam')  # Use 'clam' theme as base
        
        # Configure styles
        style.configure('TFrame', background=COLORS["background"])
        style.configure('TLabelframe', background=COLORS["background"])
        style.configure('TLabelframe.Label', background=COLORS["background"], foreground=COLORS["text"], font=(FONT_FAMILY, 10, 'bold'))
        style.configure('TButton', background=COLORS["primary"], foreground='white', font=(FONT_FAMILY, 9))
        style.map('TButton', background=[('active', COLORS["secondary"])])
        style.configure('TLabel', background=COLORS["background"], foreground=COLORS["text"], font=(FONT_FAMILY, 9))
        style.configure('TCheckbutton', background=COLORS["background"], foreground=COLORS["text"], font=(FONT_FAMILY, 9))
        style.configure('TEntry', background='white', font=(FONT_FAMILY, 9))
        style.configure('Horizontal.TProgressbar', background=COLORS["secondary"])
        
        # Create a header
        header_frame = ttk.Frame(root)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        header_label = ttk.Label(header_frame, text="Phone Records File Converter", 
                               font=(FONT_FAMILY, 16, 'bold'), foreground=COLORS["primary"])
        header_label.pack()
        
        # Input files
        self.input_frame = ttk.LabelFrame(root, text="Input Files")
        self.input_frame.pack(fill="x", expand="yes", padx=20, pady=10)
        
        # Create a frame for the listbox and scrollbar
        list_frame = ttk.Frame(self.input_frame)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add listbox for multiple files
        self.file_listbox = tk.Listbox(list_frame, height=5, width=70, yscrollcommand=scrollbar.set)
        self.file_listbox.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=self.file_listbox.yview)
        
        # Buttons for file selection
        button_frame = ttk.Frame(self.input_frame)
        button_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(button_frame, text="Add Files...", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear All", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        
        # Store the list of input files
        self.input_files = []
        
        # Output directory
        self.output_frame = ttk.LabelFrame(root, text="Output Directory")
        self.output_frame.pack(fill="x", expand="yes", padx=20, pady=10)
        
        # Add a checkbox for project directory output
        self.use_project_dir = tk.BooleanVar(value=True)  # Default to using project directory
        self.project_dir_checkbox = ttk.Checkbutton(
            self.output_frame, 
            text="Use project root directory", 
            variable=self.use_project_dir,
            command=self.toggle_output_dir
        )
        self.project_dir_checkbox.pack(anchor="w", padx=5, pady=(5, 0))
        
        # Add a label to show the project directory path
        self.project_dir_path = self.get_project_root()
        self.project_dir_label = ttk.Label(
            self.output_frame, 
            text=f"Project directory: {self.project_dir_path}",
            foreground=COLORS["secondary"]
        )
        self.project_dir_label.pack(anchor="w", padx=25, pady=(0, 5))
        
        # Frame for custom output directory
        self.custom_dir_frame = ttk.Frame(self.output_frame)
        self.custom_dir_frame.pack(fill="x", padx=5, pady=5)
        
        self.output_dir = tk.StringVar()
        ttk.Label(self.custom_dir_frame, text="Custom output directory:").pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(self.custom_dir_frame, textvariable=self.output_dir, width=40).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.custom_dir_frame, text="Browse...", command=self.browse_output_dir).pack(side=tk.LEFT, padx=5)
        
        # Convert button with custom style
        style.configure(BUTTON_STYLE_CONVERT, 
                      background=COLORS["secondary"], 
                      foreground='white', 
                      font=(FONT_FAMILY, 11, 'bold'),
                      padding=10)
        style.map(BUTTON_STYLE_CONVERT, background=[('active', COLORS["primary"])])
        
        self.convert_button = ttk.Button(
            root, 
            text="Convert Files", 
            command=self.convert,
            style=BUTTON_STYLE_CONVERT
        )
        self.convert_button.pack(pady=20)
        
        # Progress bar with improved styling
        self.progress_frame = ttk.Frame(root)
        self.progress_frame.pack(fill="x", padx=20, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, 
            variable=self.progress_var, 
            maximum=100,
            style='Horizontal.TProgressbar'
        )
        self.progress_bar.pack(fill="x")
        
        self.progress_label = ttk.Label(
            self.progress_frame, 
            text="Ready to convert files",
            foreground=COLORS["text"],
            font=(FONT_FAMILY, 9, 'italic')
        )
        self.progress_label.pack(pady=5)
        
        # Status area with custom styling
        self.status_frame = ttk.LabelFrame(root, text="Status")
        self.status_frame.pack(fill="both", expand="yes", padx=20, pady=10)
        
        # Create a frame for the text widget and scrollbar
        text_frame = ttk.Frame(self.status_frame)
        text_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Status text with custom styling
        self.status_text = tk.Text(
            text_frame, 
            height=10, 
            width=70,
            font=('Consolas', 9),
            bg='white',
            fg=COLORS["text"],
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set
        )
        self.status_text.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.config(command=self.status_text.yview)
        
        # Configure text tags for colored output
        self.status_text.tag_configure("success", foreground=COLORS["success"])
        self.status_text.tag_configure("warning", foreground=COLORS["warning"])
        self.status_text.tag_configure("error", foreground=COLORS["error"])
        self.status_text.tag_configure("info", foreground=COLORS["primary"])
        
        # Add a footer with version info
        footer_frame = ttk.Frame(root)
        footer_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        version_label = ttk.Label(
            footer_frame, 
            text="v1.1.0 | Created for TextandFlex",
            font=(FONT_FAMILY, 8),
            foreground="gray"
        )
        version_label.pack(side=tk.RIGHT)
        
        # Initialize the UI state based on checkbox
        self.toggle_output_dir()
    
    def add_files(self):
        filenames = filedialog.askopenfilenames(
            title="Select Input Excel Files",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if filenames:
            for filename in filenames:
                if filename not in self.input_files:
                    self.input_files.append(filename)
                    self.file_listbox.insert(tk.END, os.path.basename(filename))
            
            # Auto-generate output directory if not set
            if not self.output_dir.get() and self.input_files and not self.use_project_dir.get():
                # Use the directory of the first file
                self.output_dir.set(os.path.dirname(self.input_files[0]))
    
    def remove_selected(self):
        selected_indices = self.file_listbox.curselection()
        if selected_indices:
            # Remove in reverse order to avoid index shifting
            for index in sorted(selected_indices, reverse=True):
                del self.input_files[index]
                self.file_listbox.delete(index)
    
    def clear_files(self):
        self.file_listbox.delete(0, tk.END)
        self.input_files = []
    
    def get_project_root(self):
        """Get the project root directory"""
        # Get the directory of the current script
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            return os.path.dirname(sys.executable)
        else:
            # Running as script
            return os.path.dirname(os.path.abspath(__file__))
    
    def toggle_output_dir(self):
        """Toggle the output directory controls based on checkbox state"""
        if self.use_project_dir.get():
            # Using project directory, disable custom directory controls
            for child in self.custom_dir_frame.winfo_children():
                child.configure(state="disabled")
            self.project_dir_label.configure(foreground=COLORS["primary"], font=(FONT_FAMILY, 9, 'bold'))
        else:
            # Using custom directory, enable controls
            for child in self.custom_dir_frame.winfo_children():
                child.configure(state="normal")
            self.project_dir_label.configure(foreground=COLORS["secondary"], font=(FONT_FAMILY, 9))
    
    def browse_output_dir(self):
        directory = filedialog.askdirectory(
            title="Select Output Directory"
        )
        if directory:
            self.output_dir.set(directory)
    
    def convert(self):
        if not self.input_files:
            messagebox.showerror("Error", "Please add at least one input file")
            return
        
        # Determine output directory based on checkbox
        if self.use_project_dir.get():
            output_dir = self.project_dir_path
        else:
            output_dir = self.output_dir.get()
            if not output_dir:
                messagebox.showerror("Error", "Please select an output directory")
                return
        
        # Make sure output directory exists
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                messagebox.showerror("Error", f"Could not create output directory: {str(e)}")
                return
        
        # Clear status text and update progress
        self.status_text.delete(1.0, tk.END)
        self.status_text.insert(tk.END, f"Converting {len(self.input_files)} files...\n", "info")
        self.progress_var.set(0)
        self.progress_label.config(text="Starting conversion...")
        self.root.update()
        
        # Disable convert button during conversion
        self.convert_button.config(state="disabled")
        
        # Start conversion in a separate thread to keep UI responsive
        threading.Thread(target=self._convert_files_thread, args=(self.input_files, output_dir), daemon=True).start()
    
    def _convert_files_thread(self, input_files, output_dir):
        try:
            total_files = len(input_files)
            results = {}
            
            for i, input_file in enumerate(input_files):
                # Update progress
                progress = (i / total_files) * 100
                self._update_progress(progress, f"Converting file {i+1} of {total_files}: {os.path.basename(input_file)}")
                
                # Generate output path
                base_name = os.path.basename(input_file)
                name, ext = os.path.splitext(base_name)
                output_file = os.path.join(output_dir, f"{name}_converted{ext}")
                
                # Convert the file
                result = convert_file(input_file, output_file)
                results[input_file] = result
                
                # Update status text
                self._update_status(input_file, result, output_file)
            
            # Complete progress
            self._update_progress(100, "Conversion complete")
            
            # Show summary message
            success_count = sum(1 for issues in results.values() if not issues)
            warning_count = sum(1 for issues in results.values() if issues)
            
            if warning_count == 0:
                messagebox.showinfo("Success", f"All {success_count} files converted successfully!")
            else:
                messagebox.showwarning("Warning", 
                                      f"{success_count} files converted successfully, {warning_count} files converted with warnings.\n\n"
                                      f"See status area for details.")
        
        except Exception as e:
            self._update_status_error(f"Error during conversion: {str(e)}")
        
        finally:
            # Re-enable convert button
            self.root.after(0, lambda: self.convert_button.config(state="normal"))
    
    def _update_progress(self, value, text):
        # Update progress bar and label in the main thread
        self.root.after(0, lambda: self.progress_var.set(value))
        self.root.after(0, lambda: self.progress_label.config(text=text))
    
    def _update_status(self, input_file, result, output_file):
        # Update status text in the main thread
        def update():
            file_name = os.path.basename(input_file)
            if not result:  # Empty list means no issues
                self.status_text.insert(tk.END, f"✅ {file_name}: Conversion successful!\n", "success")
                self.status_text.insert(tk.END, f"   Saved to: {output_file}\n")
            else:
                self.status_text.insert(tk.END, f"⚠️ {file_name}: Converted with warnings:\n", "warning")
                for issue in result:
                    self.status_text.insert(tk.END, f"   - {issue}\n", "warning")
                self.status_text.insert(tk.END, f"   Saved to: {output_file}\n")
            self.status_text.see(tk.END)
        
        self.root.after(0, update)
    
    def _update_status_error(self, error_message):
        # Update status text with error in the main thread
        def update():
            self.status_text.insert(tk.END, f"❌ Error: {error_message}\n", "error")
            self.status_text.see(tk.END)
        
        self.root.after(0, update)

if __name__ == "__main__":
    root = tk.Tk()
    app = PhoneRecordsConverterApp(root)
    root.mainloop()
