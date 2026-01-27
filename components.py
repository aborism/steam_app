import streamlit as st
import random
import os
import html
from utils import get_base64_image, get_icon_html

def get_badge_icon(attention_label: str) -> str:
    """注目度ラベルに応じたアイコン画像のHTMLタグを返す"""
    icon_name = "chest_unexplored"  # デフォルト
    
    # 宝箱（注目度）
    if "伝説の宝箱" in attention_label:
        icon_name = "legendary_treasurebox"
    elif "金の宝箱" in attention_label:
        icon_name = "gold_treasurebox"
    elif "銀の宝箱" in attention_label:
        icon_name = "silver_treasurebox"
    elif "銅の宝箱" in attention_label:
        icon_name = "bronze_treasurebox"
    elif "天秤の宝箱" in attention_label:
        icon_name = "scales_treasurebox"
    elif "魔界の宝箱" in attention_label:
        icon_name = "demon_treasurebox"
    elif "未開の宝箱" in attention_label:
        icon_name = "unexplored_treasurebox"
    elif "隠れた名作" in attention_label:
        icon_name = "gem"  # 既存アイコンがない場合はデフォルトアイコン等での代用を検討するが、今回はgemを想定
    elif "新芽" in attention_label:
        icon_name = "sprout"
    
    # 塔（期待度）
    elif "那由多の塔" in attention_label:
        icon_name = "tower_nayuta"
    elif "太陽の塔" in attention_label:
        icon_name = "tower_sun_v2" 
    elif "月の塔" in attention_label:
        icon_name = "tower_moon_v2"
    elif "星の塔" in attention_label:
        icon_name = "tower_star"
        
    path = f"img/{icon_name}.png"
    if os.path.exists(path):
        b64 = get_base64_image(path)
        # ユーザーによる手動リサイズ済みのため16pxに統一
        display_width = "16"
        
        return f'<img src="data:image/png;base64,{b64}" width="{display_width}" style="vertical-align: -2px; margin-right: 2px;">'
    return ""


def render_game_card(game: dict, col, idx: int):
    """ゲームカードをレンダリング"""
    with col:
        app_id = game.get("app_id", 0)
        
        # 画像（XSS対策: URLをエスケープ）
        img_url = html.escape(game.get("image") or "https://via.placeholder.com/460x215?text=No+Image")
        
        # レアリティ演出判定
        attention = game.get("attention_label", "")
        reveal_class = ""
        if "伝説" in attention:
            reveal_class = "reveal-legendary"
        elif "那由多" in attention:
            reveal_class = "reveal-nayuta"
        elif "金" in attention:
            reveal_class = "reveal-gold"
        elif "太陽" in attention:
            reveal_class = "reveal-sun"
            
        # 最初の4枚は優先読み込み、それ以降は遅延読み込み
        loading_attr = 'eager' if idx < 4 else 'lazy'
        priority_attr = 'fetchpriority="high"' if idx < 4 else ''
        
        if reveal_class:
             # 特殊アニメーション付き画像
             st.markdown(f'<img src="{img_url}" class="preview-image {reveal_class}" style="width:100%; object-fit:cover;" decoding="async" loading="{loading_attr}" {priority_attr}>', unsafe_allow_html=True)
        else:
             # 通常の画像
             st.markdown(f'<img src="{img_url}" class="preview-image" style="width:100%; object-fit:cover;" decoding="async" loading="{loading_attr}" {priority_attr}>', unsafe_allow_html=True)
        
        # タイトル（2行制限、XSS対策: エスケープ）
        safe_title = html.escape(game.get("title", ""))
        title_html = f'<div class="game-title">{safe_title}</div>'
        st.markdown(title_html, unsafe_allow_html=True)
        
        # バッジ行
        badges_html = '<div class="badge-row">'
        if game.get("is_jp_supported"):
            badges_html += '<span class="jp-badge">🗾 日本語あり</span>'
        
        attention = game.get("attention_label", "")
        if attention:
            badge_icon_html = get_badge_icon(attention)
            
            # レアリティに応じたglowクラスを決定
            glow_class = ""
            if "伝説" in attention or "那由多" in attention:
                glow_class = "glow-legendary"
            elif "金" in attention or "太陽" in attention:
                glow_class = "glow-gold"
            elif "隠れた名作" in attention:
                glow_class = "gem-badge"
            elif "新芽" in attention:
                glow_class = "sprout-badge"
            elif "銀" in attention or "月" in attention:
                glow_class = "glow-silver"
            
            # アイコンとテキストを表示（背景色＋エフェクト付き）
            if badge_icon_html:
                badges_html += f'<span class="attention-badge {glow_class}">{badge_icon_html}{attention}</span>'
            else:
                badges_html += f'<span class="attention-badge {glow_class}">{attention}</span>'
        badges_html += '</div>'
        st.markdown(badges_html, unsafe_allow_html=True)
        
        # 日付と価格/体験版を横並びで表示（左寄せ・GAP指定でレスポンシブ対応）
        # 日付を短縮形式（YYYY/MM/DD）に変換してスペースを節約
        date_str = game['date'].replace("年", "/").replace("月", "/").replace("日", "").rstrip("/")
        
        # Coming Soonの場合は体験版の有無、それ以外は価格を表示
        if game.get("is_coming_soon"):
            if game.get("has_demo"):
                second_col = '<span style="color: #4CAF50; font-size: 0.9em; white-space: nowrap;">🎮 体験版あり</span>'
            else:
                second_col = '<span style="color: #888; font-size: 0.9em; white-space: nowrap;">🎮 体験版なし</span>'
        else:
            second_col = f'<span style="color: #FFD700; font-size: 0.9em; white-space: nowrap;">💰 {game["price"]}</span>'
        
        date_price_html = f'''
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px; flex-wrap: wrap;">
            <span style="font-size: 0.9em; color: #ccc; white-space: nowrap;">📅 {date_str}</span>
            {second_col}
        </div>
        '''
        st.markdown(date_price_html, unsafe_allow_html=True)
        
        # レビューまたはフォロワー数
        follower_count = game.get("follower_count")
        if follower_count is not None:
            # Coming Soon: フォロワー数を表示
            st.caption(f"👥 フォロワー: {follower_count}")
        elif game["review_count"] == 0:
            st.caption("📜 日本語のレビュー数: 0")
        else:
            st.caption(f"📜 日本語のレビュー数: {game['review_count']}")
        
        # 価格（上に移動したため削除）
        
        # 秘宝の詳細（エクスパンダー）
        video_url = game.get("video_url")
        screenshots = game.get("screenshots", [])
        description = game.get("description", "")
        
        if video_url or screenshots or description:
            with st.expander("詳細を見る"):
                if description:
                    # XSS対策: 説明文をエスケープ
                    safe_description = html.escape(description)
                    st.markdown(f"_{safe_description}_")
                
                if video_url:
                    if ".m3u8" in video_url:
                        # HLS形式: クライアントサイドで動的に読み込む（リロードなし）
                        # JavaScriptでボタンクリック時にプレイヤーを生成
                        video_component_html = f'''
                        <style>
                            html,body{{margin:0;padding:0;width:100%;height:100%;overflow:hidden;background:transparent}}
                            #player-container{{width:100%;height:100%;display:flex;align-items:center;justify-content:center}}
                            #load-btn{{
                                background: linear-gradient(135deg, #3a3a5c 0%, #2a2a3c 100%);
                                border: 1px solid #5a5a7a;
                                color: #fff;
                                padding: 12px 24px;
                                border-radius: 8px;
                                cursor: pointer;
                                font-size: 14px;
                                transition: all 0.2s;
                            }}
                            #load-btn:hover{{background: linear-gradient(135deg, #4a4a6c 0%, #3a3a4c 100%);}}
                            video{{max-width:100%;max-height:100%;width:auto;height:auto;object-fit:contain;border-radius:8px;outline:none}}
                        </style>
                        <div id="player-container">
                            <button id="load-btn" onclick="loadVideo()">📺 動画を読み込む</button>
                        </div>
                        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
                        <script>
                            function loadVideo() {{
                                var container = document.getElementById('player-container');
                                container.innerHTML = '<video id="hls-video" controls autoplay></video>';
                                var video = document.getElementById('hls-video');
                                if (Hls.isSupported()) {{
                                    var hls = new Hls();
                                    hls.loadSource('{video_url}');
                                    hls.attachMedia(video);
                                }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                                    video.src = '{video_url}';
                                }}
                            }}
                        </script>
                        '''
                        st.components.v1.html(video_component_html, height=225)
                    else:
                        st.video(video_url)
                
                if screenshots:
                    # スクリーンショットを2列で表示（遅延読み込み）
                    ss_cols = st.columns(2)
                    for i, ss_url in enumerate(screenshots[:4]):
                        if ss_url:
                            # XSS対策: URLをエスケープ
                            safe_ss_url = html.escape(ss_url)
                            # loading="lazy" でネイティブ遅延読み込み
                            ss_cols[i % 2].markdown(
                                f'<img src="{safe_ss_url}" loading="lazy" style="width:100%; border-radius:4px;">',
                                unsafe_allow_html=True
                            )
        
        # 入手ボタン
        btn_type = "primary" if game.get("is_jp_supported") else "secondary"
        st.link_button("🛒 Steamで開く", game["link"], use_container_width=True, type=btn_type)


def render_magic_logo(logo_b64=None):
    """魔法エフェクト付きのロゴを表示"""
    # 20個の静的パーティクル（CSSで位置・アニメーション定義済み）
    particles = ''.join(['<div class="magic-particle"></div>' for _ in range(20)])
    
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="600">'
    else:
        logo_html = f'<h1>{get_icon_html("sword", 40)} Steam Arcana</h1>'
    
    st.markdown(f'''
    <div class="logo-magic-container">
        {particles}
        <div class="logo-content">
            {logo_html}
            <h5 style="margin-top: 10px;">膨大なアーカイブに眠る<br class="mobile-break">未知なる宝を探し出す</h5>
        </div>
    </div>
    ''', unsafe_allow_html=True)




