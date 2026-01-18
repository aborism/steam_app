import streamlit as st
import os
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
        
        # 画像
        img_url = game.get("image") or "https://via.placeholder.com/460x215?text=No+Image"
        
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
            
        if reveal_class:
             # HTMLコンテナは削除し、直接imgタグを描画（アニメーション失敗対策）
             st.markdown(f'<img src="{img_url}" class="preview-image {reveal_class}" style="width:100%; object-fit:cover;">', unsafe_allow_html=True)
        else:
             # st.imageの代わりに統一されたクラスを持つimgタグを使用
             st.markdown(f'<img src="{img_url}" class="preview-image" style="width:100%; object-fit:cover;">', unsafe_allow_html=True)
        
        # タイトル（2行制限）
        title_html = f'<div class="game-title">{game["title"]}</div>'
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
            st.caption("📜 冒険者の記述: 0")
        else:
            st.caption(f"📜 冒険者の記述: {game['review_count']}")
        
        # 価格（上に移動したため削除）
        
        # 秘宝の詳細（エクスパンダー）
        video_url = game.get("video_url")
        screenshots = game.get("screenshots", [])
        description = game.get("description", "")
        
        if video_url or screenshots or description:
            with st.expander("詳細を見る"): # エクスパンダーのラベルにはHTMLが使えないためテキストのみ
                if description:
                    st.markdown(f"_{description}_")
                
                if video_url:
                    st.video(video_url)
                
                if screenshots:
                    # スクリーンショットを2列で表示
                    ss_cols = st.columns(2)
                    for i, ss_url in enumerate(screenshots[:4]):
                        if ss_url:
                            ss_cols[i % 2].image(ss_url, use_container_width=True)
        
        # 入手ボタン
        btn_type = "primary" if game.get("is_jp_supported") else "secondary"
        st.link_button("🛒 Steamで開く", game["link"], use_container_width=True, type=btn_type)
