# Frame Texture Paint

A lightweight Blender add-on (4.2 / 5.x) for **frame-by-frame texture animation** directly in **Texture Paint** mode.

Paint hand-drawn 2D animations right on your 3D models, manage multiple animated texture nodes in separate folders, and automatically save everything as clean PNG sequences.


https://github.com/user-attachments/assets/6735dfe4-6c8a-4724-a215-fa30f271ed55


## ✨ Features
- **Frame-by-Frame Texture Workflow:** Create blank keyframes, duplicate previous frames, or delete keys with automatic frame holding (`Hold`) across the timeline.
- **Multi-Node Support:** Switch between all `Image Texture` nodes in your active material directly from the 3D Viewport N-Panel without opening the Shader Editor.
- **Organized PNG Sequences:** Automatically saves frames (`frame_0001.png`, `frame_0002.png`, etc.) into dedicated subfolders next to your `.blend` file.
- **Timeline & Dope Sheet Sync:** Duplicate (`Shift + D`) keyframe markers on the timeline and sync them to generate the corresponding image files automatically.
- **Quick Keyframe Navigation:** Jump between existing texture keyframes with `Prev Key` / `Next Key` buttons.
- **Canvas Presets:** Choose texture resolution (`512` to `4096`) and background fill (`Transparent`, `Black`, `White`) before creating new frames.

## 📥 Download & Installation
1. Go to the **[Releases](../../releases/latest)** page and download **`frame_texture_paint.zip`** under the **Assets** section *(do not download Source code)*.
2. Open Blender (`4.2` or newer).
3. Go to **Edit → Preferences → Get Extensions** (or **Add-ons**).
4. Click the **drop-down arrow** in the top-right corner and select **Install from Disk...**
5. Select the downloaded `frame_texture_paint.zip` and enable **Frame Texture Paint**.

## 🚀 Quick Start
1. **Save your `.blend` file** first (sequences are saved relative to your project folder).
2. Add a standard **Image Texture** node to your object's material in the Shader Editor.
3. Switch the 3D Viewport to **Texture Paint** mode and open the **N-Panel → Frame Paint** tab.
4. Select your texture node from the list, choose your resolution/background, and click **New Blank Keyframe**.
5. Paint on your mesh, move to another frame on the timeline, and create or duplicate the next keyframe!

## 💡 Workflow Tips
- **Use "Duplicate Keyframe" as an Onion Skin alternative:** Since Texture Paint doesn't have built-in onion skinning, click **Duplicate Keyframe** instead of creating a blank one. This lets you use the previous drawing as a visual reference—just erase the parts you want to change and paint the next pose.
- **Start from an existing image:** If you already have a painted texture loaded into your `Image Texture` node, simply move to frame `1` (or any starting frame) and click **Duplicate Keyframe**. The add-on will safely copy it into the sequence folder as your first keyframe without altering your original file.
