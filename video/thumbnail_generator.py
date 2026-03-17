"""
Thumbnail Generator  TheScienceOfYou
Auto-generates clickable thumbnails for long-form videos.
"""

import os
import subprocess
import re


def generate_thumbnail(video_path: str, hook_text: str, subtitle: str = "",
                       output_path: str = "thumbnail.jpg", timestamp: float = 5.0) -> bool:
    """
    Generates a thumbnail from the video with text overlay.
    1280x720 JPG  YouTube standard.
    """
    try:
        # Clean text for FFmpeg
        hook_clean = re.sub(r"['\"]", "", hook_text).upper()[:40]
        sub_clean = re.sub(r"['\"]", "", subtitle).lower()[:50] if subtitle else ""
        
        # Build filter  frame + text + color grade
        filters = (
            f"scale=1280:720,"
            f"eq=brightness=0.05:contrast=1.25:saturation=1.3,"
            f"vignette=PI/4"
        )
        
        # Main hook text
        filters += (
            f",drawtext=text='{hook_clean}':"
            f"fontsize=58:fontcolor=yellow:borderw=4:bordercolor=black:"
            f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            f"x=(w-text_w)/2:y=(h-text_h)/2-30"
        )
        
        # Subtitle
        if sub_clean:
            filters += (
                f",drawtext=text='{sub_clean}':"
                f"fontsize=28:fontcolor=white:borderw=2:bordercolor=black:"
                f"fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
                f"x=(w-text_w)/2:y=(h/2)+40"
            )
        
        cmd = [
            "ffmpeg", "-ss", str(timestamp),
            "-i", video_path, "-vframes", "1",
            "-vf", filters,
            "-y", output_path
        ]
        
        subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 10000:
            print(f"[Thumbnail] Generated: {output_path}")
            return True
        
        return False
    except Exception as e:
        print(f"[Thumbnail] Error: {e}")
        return False
