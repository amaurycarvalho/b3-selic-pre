## 1. Set Tkinter window icon

- [x] 1.1 Add `import os` at the top of `b3_selic_pre.py` (if not already present)
- [x] 1.2 Add a module-level `_SCRIPT_DIR` constant resolving the script directory: `os.path.dirname(os.path.abspath(__file__))`
- [x] 1.3 In `SelicPreApp.__init__`, after `root.title(...)`, load the PNG: `img = tk.PhotoImage(file=os.path.join(_SCRIPT_DIR, "b3_selic_pre.png"))`
- [x] 1.4 Store the image as `self.icon_img = img` to prevent garbage collection
- [x] 1.5 Call `root.iconphoto(True, img)` to set the window and taskbar icon

## 2. Create desktop entry file

- [x] 2.1 Create `b3-selic-pre.desktop` at the project root with `Name`, `Exec`, `Icon`, `Type`, `Categories` fields
- [x] 2.2 Set `Icon` to the absolute path of `b3_selic_pre.png` using a comment noting the path may need adjustment
- [x] 2.3 Set `Exec` to invoke `python3` with the script path and `--gui` flag

## 3. Verify

- [x] 3.1 Run `python3 b3_selic_pre.py --gui` and confirm the window icon appears
- [x] 3.2 Run `python3 b3_selic_pre.py --gui` from a different working directory and confirm the icon still loads
- [x] 3.3 Validate the `.desktop` file with `desktop-file-validate b3-selic-pre.desktop`
