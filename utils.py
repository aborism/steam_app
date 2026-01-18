import base64
import os

def get_base64_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def get_icon_html(icon_name, width=24):
    """アイコン画像をHTMLタグとして取得"""
    path = f"img/{icon_name}.png"
    if os.path.exists(path):
        b64 = get_base64_image(path)
        return f'<img src="data:image/png;base64,{b64}" width="{width}" style="vertical-align: -4px; margin-right: 5px;">'
    return ""

