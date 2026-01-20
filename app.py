import streamlit as st
import requests
from bs4 import BeautifulSoup
import random
import time
import re
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from steam_api import get_app_details, extract_preview_urls, calc_attention_label, calc_expectation_label, get_follower_count
from utils import get_base64_image, get_icon_html
from components import render_game_card, render_magic_logo

from PIL import Image
import base64
import os

# ページ設定
try:
    icon = Image.open("icon.png")
except:
    icon = "⚔️"

st.set_page_config(page_title="Steam Arcana", page_icon=icon, layout="wide")

# アニメーション用画像の読み込み
bg_b64 = ""
adv_b64 = ""
if os.path.exists("img/dungeon_wall.png"):
    bg_b64 = get_base64_image("img/dungeon_wall.png")
if os.path.exists("img/catgirl_run.gif"):
    adv_b64 = get_base64_image("img/catgirl_run.gif")

# ----------------------------------------------------
# 🧛 カスタムCSS
# ----------------------------------------------------
st.markdown(f"""
<style>
    /* Google Fonts 読み込み */
    @import url('https://fonts.googleapis.com/css2?family=DotGothic16&family=Noto+Sans+JP:wght@400;700&display=swap');

    /* ベーススタイル（全体をドットゴシックに） */
    .stApp {{ 
        background-color: #0e0e0e; 
        color: #e0e0e0; 
        font-family: 'DotGothic16', sans-serif !important;
    }}
    
    /* コンテンツ全体の余白を詰める */
    .block-container {{
        padding-top: 2rem !important;
    }}
    
    /* タイトル・見出し */
    h1, h2, h3, h4, h5, .stButton>button, .stRadio label, .stCheckbox label {{
        font-family: 'DotGothic16', sans-serif !important;
        letter-spacing: 0.05em;
    }}

    /* 例外：ゲームタイトルと詳細は読みやすさ重視（Noto Sans JP） */
    .game-title, .streamlit-expanderContent, .element-container .stMarkdown p {{
        font-family: 'Noto Sans JP', sans-serif !important;
    }}

    /* スマホなどで改行するためのクラス */
    .mobile-break {{ display: none; }}
    @media (max-width: 640px) {{
        .mobile-break {{ display: block; }}
    }}

    /* ボタンスタイル（モダン・フラッシュ） */
    /* ボタンスタイル（強制適用） */
    div[data-testid="stButton"] button, 
    div.stButton button {{
        background: linear-gradient(135deg, #FFD700 0%, #DAA520 50%, #B8860B 100%) !important;
        border: 1px solid #FFF8DC !important; 
        border-radius: 8px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4);
        transition: all 0.2s ease;
    }}
    
    /* ボタン内のテキスト（最重要：pタグをターゲット） */
    div[data-testid="stButton"] button p {{
        font-family: 'DotGothic16', sans-serif !important;
        font-weight: normal !important;
        font-size: 16px !important; /* 18pxから16pxに変更 */
        color: #000000 !important; 
        text-shadow: 0px 1px 1px rgba(255, 255, 255, 0.4);
        margin: 0 !important; /* 余計なマージン削除 */
    }} 
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.4);
        transition: all 0.2s ease;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px); 
        background: linear-gradient(135deg, #FFF8DC 0%, #FFD700 100%);
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.6), inset 0 0 10px rgba(255, 255, 255, 0.5); 
        color: #1a1a1a;
        border-color: #FFFFFF;
    }}
    .stButton>button:active {{
        transform: translateY(1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }}

    /* カラム背景（ガラス風） */
    div[data-testid="column"] {{ 
        background-color: rgba(20, 20, 20, 0.85); 
        padding: 10px; 
        border-radius: 8px; 
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #ffffff;
        backdrop-filter: blur(5px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    
    /* ゲームカード */
    .game-card {{
        position: relative;
        min-height: 360px;
        padding-bottom: 10px;
    }}
    
    /* タイトル（2行で切り捨て） */
    .game-title {{
        font-weight: bold;
        font-size: 1em;
        height: 2.6em;
        line-height: 1.3em;
        overflow: hidden;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        text-overflow: ellipsis;
        margin-bottom: 4px;
    }}
    
/* アニメーション定義 */
/* walkアニメーションはGIF化したため削除 */

@keyframes slide-bg {{
    from {{ background-position: 0 0; }}
    to {{ background-position: -100px 0; }}
}}
/* 洗練されたブラーフェードイン（Stylish Blur-In）+ 強化エフェクト */
@keyframes stylish-reveal-gold {{
    0% {{
        filter: blur(20px) brightness(1.2);
        opacity: 0.6; /* 完全に消さず、少し透けさせる */
        transform: scale(1.05) translateY(10px);
    }}
    100% {{
        filter: blur(0) brightness(1);
        opacity: 1;
        transform: scale(1) translateY(0);
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.6), 0 0 30px rgba(255, 140, 0, 0.4); /* 強めの金オーラ */
    }}
}}

@keyframes gold-shimmer {{
    0%, 100% {{ 
        filter: brightness(1); 
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.6), 0 0 30px rgba(255, 140, 0, 0.4);
    }}
    50% {{ 
        filter: brightness(1.15); 
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.9), 0 0 40px rgba(255, 140, 0, 0.6); /* 呼吸するように輝く */
    }}
}}

@keyframes stylish-reveal-legendary {{
    0% {{
        filter: blur(30px) brightness(1.5) hue-rotate(30deg);
        opacity: 0.6;
        transform: scale(1.1) translateY(15px);
    }}
    100% {{
        filter: blur(0) brightness(1) hue-rotate(0deg);
        opacity: 1;
        transform: scale(1) translateY(0);
        box-shadow: 
            0 0 15px #ff0000, 
            0 0 30px #00ff00, 
            0 0 45px #0000ff; /* 派手なRGB影 */
    }}
}}

/* 伝説・那由多用の高速レインボーサイクル */
@keyframes legendary-cycle {{
    0% {{ box-shadow: 0 0 15px #ff0000, 0 0 30px #ffff00; }}
    25% {{ box-shadow: 0 0 15px #00ff00, 0 0 30px #00ffff; }}
    50% {{ box-shadow: 0 0 15px #0000ff, 0 0 30px #ff00ff; }}
    75% {{ box-shadow: 0 0 15px #ff00ff, 0 0 30px #ff0000; }}
    100% {{ box-shadow: 0 0 15px #ff0000, 0 0 30px #ffff00; }}
}}

/* 冒険者アニメーションコンテナ */
.adventure-container {{
    width: 100%;
    height: 100px;
    background-image: url("data:image/png;base64,{bg_b64}");
    background-repeat: repeat-x;
    background-size: 100px 100px;
    animation: slide-bg 1s linear infinite;
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 10px;
    border: 2px solid #555;
    box-shadow: inset 0 0 20px rgba(0,0,0,0.8);
}}
.adventurer {{
    width: 64px;
    height: 64px;
    background-image: url("data:image/gif;base64,{adv_b64}");
    background-size: contain;
    background-repeat: no-repeat;
    background-position: center;
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    left: 0%; /* 初期位置は左端 */
    transition: left 0.3s ease-out; /* 滑らかに移動 */
}}

/* レアリティ演出用クラス（初期状態） */
.reveal-legendary, .reveal-nayuta, .reveal-gold, .reveal-sun {{
    filter: blur(20px);
    opacity: 0.6; /* 最初から少し見えている状態 */
    width: 100% !important;
    display: block;
    transition: filter 0.5s ease-out, opacity 0.5s ease-out; /* スムーズな遷移 */
}}

/* アニメーション適用（派手さを強化） */
.reveal-gold.animated, .reveal-sun.animated {{
    animation: 
        stylish-reveal-gold 0.8s cubic-bezier(0.22, 1, 0.36, 1) forwards,
        gold-shimmer 3s ease-in-out 0.8s infinite; /* 出現後に輝き続ける */
}}

.reveal-legendary.animated, .reveal-nayuta.animated {{
    animation: 
        stylish-reveal-legendary 1.0s cubic-bezier(0.22, 1, 0.36, 1) forwards,
        legendary-cycle 2s linear 1.0s infinite; /* 高速で色が変化 */
}}
    
    /* バッジ行（高さ固定でレイアウト崩れ防止） */
    .badge-row {{
        display: flex;
        flex-wrap: wrap;
        align-items: flex-start; /* 上寄せ */
        gap: 4px;
        margin-bottom: 6px;
        min-height: 52px; /* 2行分確保して揃える */
    }}
    
    /* 日本語ありバッジ */
    .jp-badge {{ 
        background-color: #1a1a2e; 
        border: 1px solid #b71c1c;
        color: #ffcdd2; 
        padding: 2px 8px; 
        border-radius: 4px; 
        font-size: 0.7em; 
        font-weight: bold;
        white-space: nowrap;
    }}
    
    /* 注目度バッジ */
    .attention-badge {{
        background: linear-gradient(135deg, #2d1f3d, #1a1a2e);
        border: 1px solid #9c27b0;
        color: #e1bee7;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7em;
        font-weight: bold;
        white-space: nowrap;
    }}
    
    /* レアリティ別エフェクト（共用：統一感重視・控えめな発光） */
    
    /* 銀・月の塔エフェクト（静かな輝き） */
    .glow-silver {{
        box-shadow: 0 0 5px rgba(192, 192, 192, 0.4);
        border-color: rgba(192, 192, 192, 0.6) !important;
    }}
    
    /* 金・太陽の塔エフェクト（ゆっくりとした呼吸） */
    .glow-gold {{
        box-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
        animation: glow-pulse 3s ease-in-out infinite;
        border-color: rgba(255, 215, 0, 0.8) !important;
    }}
    
    /* 伝説・那由多の塔エフェクト（虹色の微光） */
    .glow-legendary {{
        position: relative;
        z-index: 1;
        overflow: hidden;
        box-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
        border: none !important; /* ボーダーは疑似要素で表現 */
    }}
    .glow-legendary::before {{
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(45deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
        background-size: 400%;
        z-index: -1;
        filter: blur(4px);
        animation: rainbow-flow 12s linear infinite; /* ゆっくりと色が流れる */
        opacity: 0.5;
        border-radius: 4px;
        margin: -2px; /* ボーダーのように外側に広げる */
    }}
    
    /* 統一されたパルスアニメーション */
    @keyframes glow-pulse {{
        0%, 100% {{ box-shadow: 0 0 5px rgba(255, 215, 0, 0.4); }}
        50% {{ box-shadow: 0 0 12px rgba(255, 215, 0, 0.7); }}
    }}
    
    /* 虹色フローアニメーション */
    @keyframes rainbow-flow {{
        0% {{ background-position: 0 0; }}
        50% {{ background-position: 100% 0; }}
        100% {{ background-position: 0 0; }}
    }}
    
    /* 隠れた名作バッジ */
    .gem-badge {{
        background: linear-gradient(135deg, #1a3a1a, #0d2d0d);
        border: 1px solid #4caf50;
        color: #a5d6a7;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7em;
        font-weight: bold;
        animation: pulse 2s infinite;
    }}
    
    /* 新芽バッジ */
    .sprout-badge {{
        background: linear-gradient(135deg, #1a2a1a, #0d1d0d);
        border: 1px solid #81c784;
        color: #c8e6c9;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.7em;
        font-weight: bold;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ box-shadow: 0 0 5px rgba(76, 175, 80, 0.5); }}
        50% {{ box-shadow: 0 0 15px rgba(76, 175, 80, 0.8); }}
    }}
    
    /* プレビュー画像スタイル */
    .preview-image {{
        border-radius: 6px;
        margin-bottom: 5px;
        border: 1px solid #444;
        width: 100%;
        aspect-ratio: 460 / 215;
        object-fit: cover;
    }}
    
    /* 詳細エクスパンダー */
    .streamlit-expanderHeader {{
        background-color: #2a2a2a !important;
        border-radius: 5px !important;
    }}
    
    /* 動画コンテナ */
    .video-container {{
        margin-bottom: 10px;
        border-radius: 8px;
        overflow: hidden;
    }}
    
    /* スクリーンショットギャラリー */
    .screenshot-gallery {{
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 10px;
    }}
    
    .screenshot-gallery img {{
        width: 200px;
        height: 112px;
        object-fit: cover;
        border-radius: 4px;
        border: 1px solid #555;
    }}
    
    /* ロゴ背景のマナエフェクト */
    @keyframes mana-rise {{
        0% {{ transform: translateY(0) scale(0.3); opacity: 0; }}
        30% {{ opacity: 1; }}
        100% {{ transform: translateY(-80px) scale(0); opacity: 0; }}
    }}
    
    @keyframes logo-aura {{
        0%, 100% {{ filter: drop-shadow(0 0 2px rgba(100, 149, 237, 0.15)); }}
        50% {{ filter: drop-shadow(0 0 8px rgba(138, 43, 226, 0.25)); }}
    }}
    
    .logo-magic-container {{
        position: relative;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        margin-top: -20px;
        padding: 50px 0;
        overflow: hidden;
    }}
    
    .magic-particle {{
        position: absolute;
        border-radius: 50%;
        opacity: 0;
        animation: mana-rise 4s infinite ease-out;
        z-index: 0;
    }}
    
    /* 20個のマナパーティクル - より派手に */
    .magic-particle:nth-child(1) {{ left: 5%; top: 85%; width: 10px; height: 10px; background: #6495ED; box-shadow: 0 0 15px #6495ED, 0 0 30px #6495ED; animation-delay: 0s; }}
    .magic-particle:nth-child(2) {{ left: 15%; top: 90%; width: 8px; height: 8px; background: #8A2BE2; box-shadow: 0 0 12px #8A2BE2, 0 0 25px #8A2BE2; animation-delay: 0.2s; }}
    .magic-particle:nth-child(3) {{ left: 25%; top: 80%; width: 12px; height: 12px; background: #FFFFFF; box-shadow: 0 0 20px #FFFFFF, 0 0 40px #87CEEB; animation-delay: 0.4s; }}
    .magic-particle:nth-child(4) {{ left: 35%; top: 88%; width: 9px; height: 9px; background: #9370DB; box-shadow: 0 0 15px #9370DB, 0 0 30px #9370DB; animation-delay: 0.6s; }}
    .magic-particle:nth-child(5) {{ left: 45%; top: 82%; width: 11px; height: 11px; background: #4169E1; box-shadow: 0 0 18px #4169E1, 0 0 35px #4169E1; animation-delay: 0.8s; }}
    .magic-particle:nth-child(6) {{ left: 55%; top: 86%; width: 8px; height: 8px; background: #8A2BE2; box-shadow: 0 0 12px #8A2BE2, 0 0 25px #8A2BE2; animation-delay: 1s; }}
    .magic-particle:nth-child(7) {{ left: 65%; top: 92%; width: 10px; height: 10px; background: #FFFFFF; box-shadow: 0 0 15px #FFFFFF, 0 0 30px #ADD8E6; animation-delay: 1.2s; }}
    .magic-particle:nth-child(8) {{ left: 75%; top: 84%; width: 7px; height: 7px; background: #6495ED; box-shadow: 0 0 10px #6495ED, 0 0 20px #6495ED; animation-delay: 1.4s; }}
    .magic-particle:nth-child(9) {{ left: 85%; top: 88%; width: 12px; height: 12px; background: #9370DB; box-shadow: 0 0 20px #9370DB, 0 0 40px #9370DB; animation-delay: 1.6s; }}
    .magic-particle:nth-child(10) {{ left: 95%; top: 80%; width: 9px; height: 9px; background: #4169E1; box-shadow: 0 0 15px #4169E1, 0 0 30px #4169E1; animation-delay: 1.8s; }}
    .magic-particle:nth-child(11) {{ left: 10%; top: 95%; width: 6px; height: 6px; background: #FFFFFF; box-shadow: 0 0 10px #FFFFFF, 0 0 20px #87CEEB; animation-delay: 2s; }}
    .magic-particle:nth-child(12) {{ left: 20%; top: 87%; width: 11px; height: 11px; background: #8A2BE2; box-shadow: 0 0 18px #8A2BE2, 0 0 35px #8A2BE2; animation-delay: 2.2s; }}
    .magic-particle:nth-child(13) {{ left: 30%; top: 93%; width: 8px; height: 8px; background: #6495ED; box-shadow: 0 0 12px #6495ED, 0 0 25px #6495ED; animation-delay: 2.4s; }}
    .magic-particle:nth-child(14) {{ left: 40%; top: 78%; width: 10px; height: 10px; background: #9370DB; box-shadow: 0 0 15px #9370DB, 0 0 30px #9370DB; animation-delay: 2.6s; }}
    .magic-particle:nth-child(15) {{ left: 50%; top: 90%; width: 13px; height: 13px; background: #FFFFFF; box-shadow: 0 0 22px #FFFFFF, 0 0 45px #ADD8E6; animation-delay: 2.8s; }}
    .magic-particle:nth-child(16) {{ left: 60%; top: 85%; width: 7px; height: 7px; background: #4169E1; box-shadow: 0 0 10px #4169E1, 0 0 20px #4169E1; animation-delay: 3s; }}
    .magic-particle:nth-child(17) {{ left: 70%; top: 95%; width: 9px; height: 9px; background: #8A2BE2; box-shadow: 0 0 15px #8A2BE2, 0 0 30px #8A2BE2; animation-delay: 3.2s; }}
    .magic-particle:nth-child(18) {{ left: 80%; top: 82%; width: 11px; height: 11px; background: #6495ED; box-shadow: 0 0 18px #6495ED, 0 0 35px #6495ED; animation-delay: 3.4s; }}
    .magic-particle:nth-child(19) {{ left: 90%; top: 90%; width: 8px; height: 8px; background: #FFFFFF; box-shadow: 0 0 12px #FFFFFF, 0 0 25px #87CEEB; animation-delay: 3.6s; }}
    .magic-particle:nth-child(20) {{ left: 50%; top: 98%; width: 14px; height: 14px; background: #9370DB; box-shadow: 0 0 25px #9370DB, 0 0 50px #9370DB; animation-delay: 3.8s; }}
    
    .logo-content {{
        position: relative;
        z-index: 1;
        animation: logo-aura 3s infinite ease-in-out;
    }}
    
    /* トップに戻るボタン */
    .scroll-to-top {{
        position: fixed;
        bottom: 40px;
        right: 40px;
        width: 50px;
        height: 50px;
        background: linear-gradient(135deg, #FFD700 0%, #DAA520 50%, #B8860B 100%);
        border: 2px solid #FFF8DC;
        border-radius: 50%;
        cursor: pointer;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        color: #000;
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.4);
    }}
    .scroll-to-top.visible {{
        opacity: 1;
        visibility: visible;
    }}
    .scroll-to-top:hover {{
        transform: translateY(-3px) scale(1.1);
        background: linear-gradient(135deg, #FFF8DC 0%, #FFD700 100%);
        box-shadow: 0 6px 20px rgba(255, 215, 0, 0.6), 0 0 30px rgba(255, 215, 0, 0.3);
    }}
    .scroll-to-top:active {{
        transform: translateY(-1px) scale(1.05);
    }}
    
    @media (max-width: 640px) {{
        .scroll-to-top {{
            bottom: 20px;
            right: 20px;
            width: 45px;
            height: 45px;
            font-size: 20px;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# アニメーション用JavaScript読み込み
if os.path.exists("reveal_animation.js"):
    with open("reveal_animation.js", "r", encoding="utf-8") as f:
        js_code = f.read()
    st.components.v1.html(f"<script>{js_code}</script>", height=0)

# トップに戻るボタン（親ドキュメントに挿入）
scroll_to_top_html = """
<script>
(function() {
    try {
        // 親ドキュメントを取得
        var parentDoc = window.parent.document;
        
        // 既存のボタンがあれば削除
        var existingBtn = parentDoc.getElementById('scroll-to-top-btn-main');
        if (existingBtn) {
            existingBtn.remove();
        }
        
        // 既存のスタイルがあれば削除
        var existingStyle = parentDoc.getElementById('scroll-to-top-style');
        if (existingStyle) {
            existingStyle.remove();
        }
        
        // CSSを親ドキュメントに追加
        var style = parentDoc.createElement('style');
        style.id = 'scroll-to-top-style';
        style.textContent = `
            #scroll-to-top-btn-main {
                position: fixed;
                bottom: 20px;
                left: 20px; /* 右側(right)から左側(left)に変更 */
                width: 40px;
                height: 40px;
                background: rgba(50, 50, 50, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                cursor: pointer;
                opacity: 0;
                visibility: hidden;
                transition: all 0.3s ease;
                z-index: 99999;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 16px;
                color: rgba(255, 255, 255, 0.8);
                font-family: sans-serif;
                backdrop-filter: blur(4px);
            }
            #scroll-to-top-btn-main.visible {
                opacity: 0.7;
                visibility: visible;
            }
            #scroll-to-top-btn-main:hover {
                opacity: 1;
                background: rgba(70, 70, 70, 0.9);
                color: #fff;
            }
            @media (max-width: 640px) {
                #scroll-to-top-btn-main {
                    bottom: 80px;
                    left: 10px; /* スマホでも左側 */
                    width: 36px;
                    height: 36px;
                    font-size: 14px;
                }
            }
        `;
        parentDoc.head.appendChild(style);
        
        // ボタンを作成して親ドキュメントのbodyに追加
        var btn = parentDoc.createElement('div');
        btn.id = 'scroll-to-top-btn-main';
        btn.innerHTML = '▲';
        btn.title = 'トップに戻る';
        parentDoc.body.appendChild(btn);
        
        // スクロールコンテナを取得（section.stMainを最優先）
        var scrollContainer = parentDoc.querySelector('section.stMain') ||
                              parentDoc.querySelector('section.main') ||
                              parentDoc.querySelector('[data-testid="stAppViewContainer"]') ||
                              parentDoc.documentElement;
        
        function checkScroll() {
            // section.stMainのスクロール位置を直接取得
            var stMain = parentDoc.querySelector('section.stMain');
            var scrollTop = 0;
            
            if (stMain) {
                scrollTop = stMain.scrollTop;
            }
            
            // 他のコンテナも確認
            scrollTop = Math.max(
                scrollTop,
                scrollContainer.scrollTop || 0,
                parentDoc.documentElement.scrollTop || 0,
                parentDoc.body.scrollTop || 0,
                window.parent.scrollY || 0
            );
            
            if (scrollTop > 300) {
                btn.classList.add('visible');
            } else {
                btn.classList.remove('visible');
            }
        }
        
        // スクロールイベントをリッスン（stMainを最優先）
        var stMainContainer = parentDoc.querySelector('section.stMain');
        if (stMainContainer) {
            stMainContainer.addEventListener('scroll', checkScroll);
        }
        scrollContainer.addEventListener('scroll', checkScroll);
        window.parent.addEventListener('scroll', checkScroll);
        
        // 定期的にチェック（Streamlitの動的更新対策）
        setInterval(checkScroll, 300);
        
        // クリックでトップへスクロール
        btn.addEventListener('click', function() {
            // section.stMainを最優先でスクロール
            var stMain = parentDoc.querySelector('section.stMain');
            if (stMain) {
                stMain.scrollTo({ top: 0, behavior: 'smooth' });
            }
            scrollContainer.scrollTo({ top: 0, behavior: 'smooth' });
            parentDoc.documentElement.scrollTo({ top: 0, behavior: 'smooth' });
            window.parent.scrollTo({ top: 0, behavior: 'smooth' });
        });
        
        checkScroll();
        
    } catch (e) {
        console.error('Scroll to top button error:', e);
    }
})();
</script>
"""
st.components.v1.html(scroll_to_top_html, height=0)

# ----------------------------------------------------
# 🎨 タイトルエリア
# ----------------------------------------------------

# タイトル（中央揃え・魔法エフェクト付き）
if os.path.exists("img/logo_steam_arcana_original.png"):
    logo_b64 = get_base64_image("img/logo_steam_arcana_original.png")
    render_magic_logo(logo_b64)
else:
    render_magic_logo(None) # デフォルトロゴ
st.divider()

# ジャンル定義 (JSONから読み込み)
def load_tags():
    with open("tags.json", "r", encoding="utf-8") as f:
        categories = json.load(f)
    # カテゴリを統合してフラットな辞書に変換
    tags = {}
    for category_tags in categories.values():
        tags.update(category_tags)
    return tags, categories  # カテゴリ情報も返す

TAGS, TAG_CATEGORIES = load_tags()

# カテゴリアイコン
CATEGORY_ICONS = {
    "基本": "📦",
    "人気・システム": "⭐",
    "シューティング": "🔫",
    "雰囲気・テーマ": "🎭",
    "建設・管理": "🏗️",
    "その他": "📁"
}

# ============================================
# 設定エリア（2列×3行グリッド・中央寄せ）
# ============================================
_, settings_area, _ = st.columns([1, 3, 1])

with settings_area:
    # ----------------------------
    # 常に表示する主要設定
    # ----------------------------
    
    # 1. 探索方法（ラジオボタン）
    search_mode = st.radio(
        "🧭 探索先",
        ["🔮 未来", "🗺️ 最新", "📜 古代"],
        index=1,
        help="未来: Coming Soon / 最新: 最新リリース / 古代: ランダム探索",
        horizontal=True
    )
    is_coming_soon_mode = "未来" in search_mode
    is_treasure_mode = "古代" in search_mode
    
    # 2. 探索タグ（カテゴリ付きマルチセレクト）
    # カテゴリプレフィックス付きのタグリストを作成
    categorized_tag_options = []
    tag_display_to_key = {}  # 表示名 → 実際のキーのマッピング
    
    for category, tags_dict in TAG_CATEGORIES.items():
        icon = CATEGORY_ICONS.get(category, "📁")
        for tag_name in tags_dict.keys():
            display_name = f"{icon} {tag_name}"
            categorized_tag_options.append(display_name)
            tag_display_to_key[display_name] = tag_name
    
    selected_display_tags = st.multiselect(
        "🗺️ 探索タグ",
        categorized_tag_options,
        default=[],
        help="未選択で全ジャンルを検索",
        placeholder="ジャンルを選択（空欄で全ジャンル）"
    )
    
    # 表示名を実際のタグ名に変換
    selected_tags = [tag_display_to_key[dt] for dt in selected_display_tags]
    
    # ----------------------------
    # 高度な設定（エクスパンダーに収納）
    # ----------------------------
    with st.expander("⚙️ 高度な検索設定"):
        adv_col1, adv_col2 = st.columns(2)
        
        with adv_col1:
            # 除外タグ（カテゴリ表示に対応）
            selected_exclude_display_tags = st.multiselect(
                "🚫 除外タグ",
                categorized_tag_options,
                default=[],
                help="これらのタグが含まれるゲームを除外",
                placeholder="除外するジャンルを選択"
            )
            # 表示名を実際のタグ名に変換
            exclude_tags = [tag_display_to_key[dt] for dt in selected_exclude_display_tags]
            
            # 通常モードの場合、ここに対応言語を表示
            if not is_coming_soon_mode:
                jp_mode = st.radio(
                    "🌐 対応言語",
                    ["🗾 日本語", "🌐 全言語"],
                    index=0,
                    horizontal=True
                )
        
        with adv_col2:
            # 未来検索モードの場合、ここに対応言語を表示（レビュー数は不要）
            if is_coming_soon_mode:
                jp_mode = st.radio(
                    "🌐 対応言語",
                    ["🗾 日本語", "🌐 全言語"],
                    index=0,
                    horizontal=True
                )
                review_threshold = 9999
            else:
                # レビュー数フィルター（Coming Soon以外）
                review_mode = st.select_slider(
                    "💎 レビュー数上限",
                    options=["少ない", "ふつう", "多い", "指定なし"],
                    value="指定なし",
                    help="少ない: 〜50件 / ふつう: 〜500件 / 多い: 〜5000件 / 指定なし: 制限なし"
                )
                
                if review_mode == "少ない":
                    review_threshold = 50
                elif review_mode == "ふつう":
                    review_threshold = 500
                elif review_mode == "多い":
                    review_threshold = 5000
                else:
                    review_threshold = 500000

    st.write("")  # スペーサー
    
    # 検索ボタン（全幅）
    if is_coming_soon_mode:
        search_btn = st.button("🔮 未来の章を開く", type="primary", use_container_width=True)
        treasure_btn = False
    elif is_treasure_mode:
        search_btn = False
        treasure_btn = st.button("📜 古代の章を開く", type="primary", use_container_width=True)
    else:
        treasure_btn = False
        search_btn = st.button("🗺️ 新しい章を開く", type="primary", use_container_width=True)

st.divider()

# ----------------------------------------------------
# ⚙️ 検索ロジック
# ----------------------------------------------------

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "Cookie": "wants_mature_content=1; birthtime=946652401; lastagecheckage=1-January-2000"
}


def is_genre_match(game_tag_ids: list, target_tag_ids: list, exclude_tag_ids: list, check_primary: bool = False) -> bool:
    """
    ジャンル一致判定（改善版）
    check_primary: Trueなら主要タグ（上位3つ）のみをチェック。Falseなら全タグをチェック。
    デフォルトをFalseに変更して、検索漏れを防ぐ。
    """
    # 除外タグが含まれていたらFalse
    for etid in exclude_tag_ids:
        if etid in game_tag_ids:
            return False
    
    # ターゲットタグが空なら全て許可
    if not target_tag_ids:
        return True
    
    # 主要タグ（先頭3つ）をチェックするか、全タグをチェックするか
    tags_to_check = game_tag_ids[:3] if check_primary and len(game_tag_ids) >= 3 else game_tag_ids
    
    for tid in target_tag_ids:
        if tid in tags_to_check:
            return True
    return False


def extract_app_id(url: str) -> int:
    """SteamストアURLからAppIDを抽出"""
    match = re.search(r'/app/(\d+)', url)
    return int(match.group(1)) if match else None


def search_steam_survivor(tags, exclude_tags_list, max_reviews, start_offset=0, only_japanese=True):
    """Steamストアを検索してゲームリストを取得"""
    base_url = "https://store.steampowered.com/search/results/"
    
    # タグIDを取得（配列の場合は展開）
    target_tag_ids = []
    for t in tags:
        if t in TAGS:
            tag_value = TAGS[t]
            if isinstance(tag_value, list):
                target_tag_ids.extend(tag_value)
            else:
                target_tag_ids.append(tag_value)
    
    exclude_tag_ids = []
    for t in exclude_tags_list:
        if t in TAGS:
            tag_value = TAGS[t]
            if isinstance(tag_value, list):
                exclude_tag_ids.extend(tag_value)
            else:
                exclude_tag_ids.append(tag_value)
    
    search_tag_ids = [str(tid) for tid in target_tag_ids]
    if "492" not in search_tag_ids:
        search_tag_ids.append("492")
    
    params = {
        "tags": ",".join(search_tag_ids),
        "cc": "JP", "l": "japanese",
        "category1": 998,
        "sort_by": "Released_DESC",
        "infinite": 1,
        "start": start_offset,
        "count": 50,
    }
    
    if only_japanese:
        params["supportedlang"] = "japanese"
    
    try:
        res = requests.get(base_url, params=params, headers=HEADERS)
        try:
            data = res.json()
        except:
            # APIからの応答が不正な場合は空リストを返す
            return []
        soup = BeautifulSoup(data.get("results_html", ""), "html.parser")
        rows = soup.select("a.search_result_row")
        
        games = []
        for row in rows:
            try:
                tag_str = row.get("data-ds-tagids", "[]")
                try:
                    game_tag_ids = json.loads(tag_str)
                except:
                    continue
                
                if not is_genre_match(game_tag_ids, target_tag_ids, exclude_tag_ids):
                    continue
                
                title = row.select_one(".title").text.strip()
                link = row.get("href")
                app_id = extract_app_id(link)
                
                review_count = 0
                review_desc = "レビューなし"
                review_tag = row.select_one(".search_review_summary")
                if review_tag:
                    tooltip = review_tag.get("data-tooltip-html", "")
                    # 日本語パターン
                    match = re.search(r"([\d,]+)件のユーザーレビュー", tooltip)
                    if not match:
                        # 英語パターン
                        match = re.search(r"([\d,]+)\s*user reviews", tooltip, re.IGNORECASE)
                    if not match:
                        # フォールバック: 数字の後に%が来るパターン（例: "813件84%"）
                        match = re.search(r"([\d,]+)[^\d]*[\d]+%", tooltip)
                    if not match:
                        # 最終フォールバック: 最初の大きな数字を取得
                        numbers = re.findall(r"(\d+)", tooltip)
                        if numbers:
                            # 最初の数字（レビュー数）を取得
                            review_count = int(numbers[0])
                    if match:
                        review_count = int(match.group(1).replace(",", ""))
                    
                    # レビュー概要を取得
                    desc_parts = tooltip.split("<br>")
                    if desc_parts:
                        review_desc = desc_parts[0] if len(desc_parts[0]) < 50 else "好評"
                
                if review_count > max_reviews:
                    continue
                
                img_tag = row.select_one("img")
                img_src = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
                if img_src:
                    img_src = img_src.split("?")[0].replace("capsule_sm_120", "header")
                
                price = "不明"
                if row.select_one(".discount_final_price"):
                    price = row.select_one(".discount_final_price").text.strip()
                elif row.select_one(".search_price"):
                    price_text = row.select_one(".search_price").text.strip()
                    price = "無料プレイ" if "Free" in price_text or "無料" in price_text else price_text
                
                date = ""
                date_tag = row.select_one(".search_released")
                if date_tag:
                    date = date_tag.text.strip()
                
                games.append({
                    "app_id": app_id,
                    "title": title,
                    "link": link,
                    "image": img_src,
                    "price": price,
                    "review_count": review_count,
                    "review_desc": review_desc,
                    "attention_label": calc_attention_label(review_count, review_desc),
                    "date": date,
                })
            except:
                continue
        
        return games
    except Exception as e:
        st.error(f"検索エラー: {e}")
        return []


def search_coming_soon(tags, exclude_tags_list, start_offset=0, only_japanese=True):
    """Coming Soon（近日公開）のゲームを検索"""
    base_url = "https://store.steampowered.com/search/results/"
    
    # タグIDを取得（配列の場合は展開）
    target_tag_ids = []
    for t in tags:
        if t in TAGS:
            tag_value = TAGS[t]
            if isinstance(tag_value, list):
                target_tag_ids.extend(tag_value)
            else:
                target_tag_ids.append(tag_value)
    
    exclude_tag_ids = []
    for t in exclude_tags_list:
        if t in TAGS:
            tag_value = TAGS[t]
            if isinstance(tag_value, list):
                exclude_tag_ids.extend(tag_value)
            else:
                exclude_tag_ids.append(tag_value)
    
    search_tag_ids = [str(tid) for tid in target_tag_ids]
    if "492" not in search_tag_ids:
        search_tag_ids.append("492")  # インディー
    
    params = {
        "filter": "comingsoon",  # Coming Soonフィルタ
        "tags": ",".join(search_tag_ids),
        "cc": "JP", "l": "japanese",
        "category1": 998,
        "sort_by": "Released_ASC",  # リリース予定日昇順
        "infinite": 1,
        "start": start_offset,
        "count": 50,
    }
    
    if only_japanese:
        params["supportedlang"] = "japanese"
    
    try:
        res = requests.get(base_url, params=params, headers=HEADERS)
        try:
            data = res.json()
        except:
            # APIからの応答が不正な場合は空リストを返す
            return []
        soup = BeautifulSoup(data.get("results_html", ""), "html.parser")
        rows = soup.select("a.search_result_row")
        
        games = []
        for row in rows:
            try:
                tag_str = row.get("data-ds-tagids", "[]")
                try:
                    game_tag_ids = json.loads(tag_str)
                except:
                    continue
                
                if not is_genre_match(game_tag_ids, target_tag_ids, exclude_tag_ids):
                    continue
                
                title = row.select_one(".title").text.strip()
                link = row.get("href")
                app_id = extract_app_id(link)
                
                img_tag = row.select_one("img")
                img_src = img_tag.get("src") or img_tag.get("data-src") if img_tag else None
                if img_src:
                    img_src = img_src.split("?")[0].replace("capsule_sm_120", "header")
                
                # 価格（Coming Soonは未定のことが多い）
                price = "価格未定"
                if row.select_one(".discount_final_price"):
                    price = row.select_one(".discount_final_price").text.strip()
                elif row.select_one(".search_price"):
                    price_text = row.select_one(".search_price").text.strip()
                    if price_text:
                        price = price_text
                
                # リリース予定日
                date = "Coming Soon"
                date_tag = row.select_one(".search_released")
                if date_tag:
                    date = date_tag.text.strip() or "Coming Soon"
                
                games.append({
                    "app_id": app_id,
                    "title": title,
                    "link": link,
                    "image": img_src,
                    "price": price,
                    "review_count": 0,  # Coming Soonはレビューなし
                    "review_desc": "Coming Soon",
                    "date": date,
                    "is_coming_soon": True,
                })
            except:
                continue
        
        return games
    except Exception as e:
        st.error(f"Coming Soon検索エラー: {e}")
        return []


def enrich_game_data(game: dict) -> dict:
    """APIからゲームの詳細データを取得して追加"""
    app_id = game.get("app_id")
    if not app_id:
        return game
    
    steam_data = get_app_details(app_id)
    if steam_data.get("success"):
        game["is_jp_supported"] = steam_data.get("is_japanese_supported", False)
        game["description"] = steam_data.get("short_description", "")
        
        preview = extract_preview_urls(steam_data)
        game["video_url"] = preview.get("video_url")
        game["screenshots"] = preview.get("screenshots", [])
    else:
        game["is_jp_supported"] = bool(re.search(r'[ぁ-んァ-ン]', game.get("title", "")))
        game["description"] = ""
        game["video_url"] = None
        game["screenshots"] = []
    
    # Coming Soonの場合は期待度ラベル、それ以外は注目度ラベル
    if game.get("is_coming_soon"):
        # Games-Popularity.com APIからフォロワー数を取得
        follower_count = get_follower_count(app_id)
        game["follower_count"] = follower_count
        game["attention_label"] = calc_expectation_label(follower_count)
        # 体験版の有無を追加
        if steam_data.get("success"):
            game["has_demo"] = len(steam_data.get("demos", [])) > 0
        else:
            game["has_demo"] = False
    else:
        game["attention_label"] = calc_attention_label(
            game.get("review_count", 0),
            game.get("review_desc", "")
        )
    
    return game





# ----------------------------------------------------
# 🎬 メイン処理
# ----------------------------------------------------

if search_btn or treasure_btn:
    # レートリミット: 3秒のクールダウン
    import time as _time
    if 'last_search_time' not in st.session_state:
        st.session_state.last_search_time = 0
    
    current_time = _time.time()
    cooldown_seconds = 3
    time_since_last = current_time - st.session_state.last_search_time
    
    if time_since_last < cooldown_seconds:
        remaining = int(cooldown_seconds - time_since_last) + 1
        st.warning(f"⏳ 少し待ってから再度検索してください（あと{remaining}秒）")
        st.stop()
    
    st.session_state.last_search_time = current_time
    
    use_jp_only = ("日本語" in jp_mode)
    results = []
    
    # アニメーション表示用コンテナ
    anim_placeholder = st.empty()
    
    # プログレスバーは非表示（代わりに冒険者が移動）

    # Coming Soonモードの場合
    if is_coming_soon_mode:
        # 未来検索のメッセージを表示
        anim_placeholder.markdown("""
            <div class="adventure-container">
                <div class="adventurer" style="left: 0%;"></div>
            </div>
            <div style="text-align:center; font-weight:bold; margin-bottom:10px;">未来を観測中...</div>
        """, unsafe_allow_html=True)
        
        # ランダムにオフセットを選択（少数のAPI呼び出しで済むように）
        # レート制限回避のため、探索回数を最小限に
        offset_options = [0, 50, 100]
        future_offset = random.choice(offset_options)
        
        results = search_coming_soon(
            selected_tags, exclude_tags, start_offset=future_offset, only_japanese=use_jp_only
        )
        
        # 結果がなければオフセット0で再試行
        if not results and future_offset > 0:
            time.sleep(0.3)  # レート制限回避
            results = search_coming_soon(
                selected_tags, exclude_tags, start_offset=0, only_japanese=use_jp_only
            )
        
        if results:
            st.markdown(f'#### {get_icon_html("treasure", 28)} 発見したアーティファクト ({len(results)}個)', unsafe_allow_html=True)
            st.caption("各カードの「詳細を見る」を開くと動画やスクリーンショットが確認できます")
    
    # 過去の秘宝モードの場合
    elif treasure_btn:
        status_text = st.empty()
        bar = st.progress(0)
        
        years = [2025, 2024, 2023, 2022, 2021, 2020, 2019, 2018, "???"]
        for i in range(5):
            fake_year = random.choice(years)
            status_text.markdown(f"### ⏳ 時空を移動中... {fake_year}年")
            bar.progress((i + 1) * 20)
            time.sleep(0.05)
        
        # 最低20件見つかるまで検索
        min_results = 20
        max_retries = 30  # 最大試行回数を増やす
        all_results = []
        
        for attempt in range(max_retries):
            random_offset = random.randint(0, 100) * 50  # より広い範囲から検索
            status_text.markdown(f"### 🎰 探索中: 深度 {random_offset}m (発見: {len(all_results)}個/{min_results}個)")
            
            found_games = search_steam_survivor(
                selected_tags, exclude_tags, review_threshold,
                start_offset=random_offset, only_japanese=use_jp_only
            )
            
            if found_games:
                # 重複を避けてリストに追加
                for game in found_games:
                    if game["app_id"] not in [g["app_id"] for g in all_results]:
                        all_results.append(game)
                
                # 20件以上見つかったら終了
                if len(all_results) >= min_results:
                    results = all_results
                    break
            
            time.sleep(0.3)
        
        # 見つかった分だけ表示（20件未満でも可）
        if all_results:
            results = all_results
            status_text.success(f"🎉 お宝発見！ {len(results)}個のアーティファクトを見つけたよ！")
            bar.empty()
        else:
            status_text.error("深い地層まで探しましたが、条件に合うアーティファクトが見つかりませんでした…。")
            bar.empty()
        
        if results:
            st.markdown(f'#### {get_icon_html("treasure", 28)} 発見したアーティファクト ({len(results)}個)', unsafe_allow_html=True)
            st.caption("各カードの「詳細を見る」を開くと動画やスクリーンショットが確認できます")
    
    else:
        # 通常検索モード
        anim_placeholder.markdown("""
            <div class="adventure-container">
                <div class="adventurer" style="left: 0%;"></div>
            </div>
            <div style="text-align:center; font-weight:bold; margin-bottom:10px;">お宝を探索中...</div>
        """, unsafe_allow_html=True)
        
        results = search_steam_survivor(
            selected_tags, exclude_tags, review_threshold,
            start_offset=0, only_japanese=use_jp_only
        )
        
        if results:
            st.markdown(f'#### {get_icon_html("treasure", 28)} 発見したアーティファクト ({len(results)}個)', unsafe_allow_html=True)
            st.caption("各カードの「詳細を見る」を開くと動画やスクリーンショットが確認できます")
    
    # 結果がある場合は詳細データ取得とグリッド表示
    if results:
        # 並列処理で高速化（最大8件同時取得）
        enriched_results = [None] * len(results)
        completed_count = 0
        
        def enrich_with_index(args):
            idx, game = args
            return idx, enrich_game_data(game)
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(enrich_with_index, (i, game)): i for i, game in enumerate(results)}
            
            for future in as_completed(futures):
                idx, enriched_game = future.result()
                enriched_results[idx] = enriched_game
                completed_count += 1
                
                # 冒険者の位置を更新
                progress_pct = int((completed_count / len(results)) * 85)
                anim_placeholder.markdown(f"""
                    <div class="adventure-container">
                        <div class="adventurer" style="left: {progress_pct}%;"></div>
                    </div>
                    <div style="text-align:center; font-weight:bold; margin-bottom:10px;">お宝を探索中... ({completed_count}/{len(results)})</div>
                """, unsafe_allow_html=True)
        
        # アニメーションを終了
        anim_placeholder.empty()
        
        # グリッド表示
        cols = st.columns(4)
        for i, game in enumerate(enriched_results):
            render_game_card(game, cols[i % 4], i)
            
            if (i + 1) % 4 == 0 and i + 1 < len(enriched_results):
                st.write("")
                cols = st.columns(4)
    
    elif not treasure_btn:
        st.warning("条件に合うゲームが見つかりませんでした。")