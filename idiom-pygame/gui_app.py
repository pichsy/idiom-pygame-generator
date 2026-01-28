
import tkinter as tk
from tkinter import font
import threading
from generate_level import IdiomGenerator

import json

class IdiomGameGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("成语消消乐 - 关卡生成器")
        self.root.geometry("600x750")
        
        self.current_grid = None # Store current grid for copying
        
        # Generator instance
        self.generator = IdiomGenerator(x_block_num=10, y_block_num=10, idiom_count=6)
        
        # Styling
        self.default_font = font.Font(family="Helvetica", size=18, weight="bold")
        self.small_font = font.Font(family="Helvetica", size=12)
        
        # Main container
        self.main_frame = tk.Frame(root, padx=20, pady=20)
        self.main_frame.pack(expand=True, fill="both")
        
        # Title
        self.title_label = tk.Label(self.main_frame, text="成语关卡预览 (10x10)", font=("Helvetica", 20, "bold"))
        self.title_label.pack(pady=(0, 20))
        
        # Grid Container
        self.grid_frame = tk.Frame(self.main_frame)
        self.grid_frame.pack()
        
        # Initialize grid labels
        self.cells = []
        for y in range(10):
            row_cells = []
            for x in range(10):
                cell_frame = tk.Frame(
                    self.grid_frame, 
                    width=50, 
                    height=50, 
                    borderwidth=1, 
                    relief="solid",
                    bg="#f0f0f0"
                )
                cell_frame.grid(row=y, column=x, padx=2, pady=2)
                cell_frame.pack_propagate(False) # Prevent resizing based on packed content (label)
                
                label = tk.Label(
                    cell_frame, 
                    text="", 
                    font=self.default_font,
                    bg="#ffffff",
                    fg="#333"
                )
                label.pack(expand=True, fill="both", padx=1, pady=1) # Leave 1px for frame border effect
                row_cells.append(label)
            self.cells.append(row_cells)
            
        # Info area
        self.info_label = tk.Label(self.main_frame, text="准备就绪", font=self.small_font, fg="#666")
        self.info_label.pack(pady=10)
        
        # Button area
        self.btn_frame = tk.Frame(self.main_frame)
        self.btn_frame.pack(pady=20)
        
        self.refresh_btn = tk.Button(
            self.btn_frame, 
            text="换一个 (Refresh)", 
            command=self.refresh_level,
            font=("Helvetica", 14),
            bg="#4CAF50",
            fg="black",
            padx=10,
            pady=5
        )
        self.refresh_btn.pack(side="left", padx=10)

        self.copy_btn = tk.Button(
            self.btn_frame, 
            text="复制 JSON (Copy)", 
            command=self.copy_json,
            font=("Helvetica", 14),
            bg="#2196F3",
            fg="black",
            padx=10,
            pady=5
        )
        self.copy_btn.pack(side="left", padx=10)
        
        # Initial load
        self.refresh_level()

    def refresh_level(self):
        self.refresh_btn.config(state="disabled")
        self.copy_btn.config(state="disabled")
        self.info_label.config(text="正在生成中...")
        
        # Run generation in a separate thread to prevent UI freezing
        thread = threading.Thread(target=self._generate_task)
        thread.start()

    def copy_json(self):
        if self.current_grid:
            try:
                json_str = json.dumps(self.current_grid, ensure_ascii=False)
                self.root.clipboard_clear()
                self.root.clipboard_append(json_str)
                self.root.update() # Required to finalize clipboard update on some systems
                self.info_label.config(text="已复制到剪贴板！")
            except Exception as e:
                self.info_label.config(text=f"复制失败: {str(e)}")

    def _generate_task(self):
        try:
            grid, words = self.generator.generate()
            # Update UI on main thread
            self.root.after(0, lambda: self._update_ui(grid, words))
        except Exception as e:
            self.root.after(0, lambda: self._show_error(str(e)))

    def _update_ui(self, grid, words):
        if not grid:
            self.info_label.config(text="生成失败，请重试")
            self.refresh_btn.config(state="normal")
            self.copy_btn.config(state="normal")
            return
            
        self.current_grid = grid # Save for copy
        
        for y in range(10):
            for x in range(10):
                content = grid[y][x]
                label = self.cells[y][x]
                
                if content:
                    if content.startswith('['):
                        # Hidden word (e.g. [龙])
                        text = content.strip('[]')
                        label.config(text=text, fg="#f00", bg="#f0f0f0") # Red text for hidden
                    else:
                        # Visible word
                        label.config(text=content, fg="#000", bg="#fff")
                else:
                    # Empty cell
                    label.config(text="  ", bg="#fafafa")
        
        word_list_str = " | ".join(words)
        self.info_label.config(text=f"包含成语: {word_list_str}")
        self.refresh_btn.config(state="normal")
        self.copy_btn.config(state="normal")

    def _show_error(self, error_msg):
        self.info_label.config(text=f"错误: {error_msg}")
        self.refresh_btn.config(state="normal")
        self.copy_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = IdiomGameGUI(root)
    root.mainloop()
