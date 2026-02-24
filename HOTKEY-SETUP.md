# Global Hotkey Setup

The `keyboard` library requires root privileges on Linux, which is not ideal for a user application.

## Recommended: Use Your Desktop Environment's Native Shortcuts

### KDE Plasma (Wayland/X11)

1. Open **System Settings** → **Shortcuts** → **Custom Shortcuts**
2. Click **Edit** → **New** → **Global Shortcut** → **Command/URL**
3. **Trigger** tab: Set your hotkey (e.g., `Super+Shift+T`)
4. **Action** tab: Set command:
   ```bash
   /home/ak/ScreenOCR.AppImage trigger
   # Or if using from source:
   /home/ak/Documents/OCR/venv-sys/bin/python /home/ak/Documents/OCR/main.py trigger
   ```
5. Click **Apply**

### GNOME (Wayland/X11)

1. Open **Settings** → **Keyboard** → **Keyboard Shortcuts**
2. Scroll to bottom, click **+ (Add Custom Shortcut)**
3. **Name:** ScreenOCR
4. **Command:** `/home/ak/ScreenOCR.AppImage trigger`
5. Click **Add**
6. Click on the shortcut row and press your desired key combination

### XFCE

1. Open **Settings** → **Keyboard** → **Application Shortcuts**
2. Click **+ Add**
3. Enter command: `/home/ak/ScreenOCR.AppImage trigger`
4. Press your desired key combination

### i3/Sway

Add to your config file (`~/.config/i3/config` or `~/.config/sway/config`):

```bash
bindsym $mod+Shift+t exec /home/ak/ScreenOCR.AppImage trigger
```

Then reload: `i3-msg reload` or `swaymsg reload`

---

## Alternative: Run Daemon with Sudo (Not Recommended)

If you really want to use the daemon mode:

```bash
sudo ./ScreenOCR.AppImage daemon start
```

**Why this is not recommended:**
- Running GUI apps as root is a security risk
- The OCR overlay window won't appear correctly
- Screenshot tools may not work properly under sudo

---

## Future: D-Bus Integration

A future version may integrate with desktop environments via D-Bus, which:
- Doesn't require root
- Works properly on Wayland
- Integrates with system settings

For now, using your DE's native shortcuts is the best approach.
