"""
Steam API 統合モジュール
- Steam Store API: ゲーム詳細（日本語対応、動画、スクショ）
- レビュー数ベースの注目度ラベル生成
"""

import requests
import time
from functools import lru_cache

# リクエストヘッダー
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
}


@lru_cache(maxsize=500)
def get_app_details(app_id: int) -> dict:
    """
    Steam Store API からゲーム詳細を取得
    
    Returns:
        {
            "success": bool,
            "name": str,
            "short_description": str,
            "is_japanese_supported": bool,
            "header_image": str,
            "movies": [{"webm": {"480": url}, "thumbnail": url}, ...],
            "screenshots": [{"path_thumbnail": url, "path_full": url}, ...],
            "genres": [{"id": str, "description": str}, ...],
            "release_date": {"coming_soon": bool, "date": str},
            "recommendations": int (レビュー数)
        }
    """
    url = f"https://store.steampowered.com/api/appdetails"
    params = {"appids": app_id, "l": "japanese", "cc": "JP"}
    
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = res.json()
        
        app_data = data.get(str(app_id), {})
        if not app_data.get("success"):
            return {"success": False}
        
        info = app_data.get("data", {})
        
        # 日本語対応チェック
        supported_langs = info.get("supported_languages", "").lower()
        is_japanese = "japanese" in supported_langs or "日本語" in supported_langs
        
        # レビュー数（推奨数から取得）
        recommendations = info.get("recommendations", {}).get("total", 0)
        
        return {
            "success": True,
            "name": info.get("name", ""),
            "short_description": info.get("short_description", ""),
            "is_japanese_supported": is_japanese,
            "header_image": info.get("header_image", ""),
            "movies": info.get("movies", []),
            "screenshots": info.get("screenshots", []),
            "genres": info.get("genres", []),
            "release_date": info.get("release_date", {}),
            "recommendations": recommendations,
            "demos": info.get("demos", []),  # 体験版情報
        }
    except Exception as e:
        print(f"Steam API Error for {app_id}: {e}")
        return {"success": False}


def get_app_reviews_summary(app_id: int) -> dict:
    """
    Steam Reviews API からレビュー概要を取得
    
    Returns:
        {
            "success": bool,
            "total_positive": int,
            "total_negative": int,
            "total_reviews": int,
            "review_score_desc": str (例: "非常に好評", "好評", "賛否両論")
        }
    """
    url = f"https://store.steampowered.com/appreviews/{app_id}"
    params = {
        "json": 1,
        "language": "all",
        "purchase_type": "all",
        "num_per_page": 0,  # レビュー本文は不要
    }
    
    try:
        res = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = res.json()
        
        if not data.get("success"):
            return {"success": False}
        
        summary = data.get("query_summary", {})
        total_positive = summary.get("total_positive", 0)
        total_negative = summary.get("total_negative", 0)
        total_reviews = summary.get("total_reviews", 0)
        review_score_desc = summary.get("review_score_desc", "")
        
        return {
            "success": True,
            "total_positive": total_positive,
            "total_negative": total_negative,
            "total_reviews": total_reviews,
            "review_score_desc": review_score_desc,
        }
    except Exception as e:
        print(f"Steam Reviews API Error for {app_id}: {e}")
        return {"success": False}


@lru_cache(maxsize=500)
def get_follower_count(app_id: int) -> int:
    """
    Games-Popularity.com API からフォロワー数を取得
    
    Returns:
        フォロワー数（取得失敗時は0）
    """
    url = f"https://games-popularity.com/swagger/api/game/followers/{app_id}"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # 最新のフォロワー数を取得（historyの最初の要素）
            followers_list = data.get("history", [])
            if followers_list and len(followers_list) > 0:
                return followers_list[0].get("followers", 0)
        return 0
    except Exception as e:
        print(f"Games-Popularity API Error for {app_id}: {e}")
        return 0


def calc_attention_label(review_count: int, review_desc: str = "") -> str:
    """
    注目度ラベルを計算（宝箱テーマ・レビュー評価基準）
    
    条件:
    - 📦 未開の宝箱: レビュー0件
    - 🥉 銅の宝箱: やや好評
    - 🥈 銀の宝箱: 好評
    - 🥇 金の宝箱: 非常に好評
    - ⚡ 伝説の宝箱: 圧倒的好評
    - ⚖️ 天秤の宝箱: 賛否両論
    - 🔥 魔界の宝箱: 不評～圧倒的不評
    """
    if review_count == 0:
        return "未開の宝箱"
    
    # レビュー評価文字列に基づいて判定
    review_lower = review_desc.lower()
    
    # 圧倒的好評（最優先）
    if "overwhelmingly positive" in review_lower or "圧倒的に好評" in review_desc:
        return "伝説の宝箱"
    
    # 隠れた名作（レビュー100件以下 && 非常に好評以上）
    # ※ 圧倒的好評は上で判定済みなので、ここは「非常に好評」が対象
    is_very_positive = "very positive" in review_lower or "非常に好評" in review_desc
    if is_very_positive and review_count <= 100:
        return "隠れた名作"

    # 新芽（レビュー10件以下 && 好評以上）
    # ※ 圧倒的好評・非常に好評・隠れた名作は判定済み
    is_positive = "positive" in review_lower or "好評" in review_desc
    if is_positive and review_count <= 10:
        return "新芽"
    
    # 非常に好評
    elif is_very_positive:
        return "金の宝箱"
    
    # やや好評
    elif "mostly positive" in review_lower or "やや好評" in review_desc:
        return "銅の宝箱"
    
    # 好評（Positive、ただし上記以外）
    elif is_positive:
        return "銀の宝箱"
    
    # 賛否両論
    elif "mixed" in review_lower or "賛否両論" in review_desc:
        return "天秤の宝箱"
    
    # 不評系（Negative, Mostly Negative, Overwhelmingly Negative）
    elif "negative" in review_lower or "不評" in review_desc:
        return "魔界の宝箱"
    
    # その他（データが不明瞭な場合）
    else:
        return "銀の宝箱"  # デフォルトは銀


def calc_expectation_label(follower_count: int) -> str:
    """
    期待度ラベルを計算（Coming Soon用・塔テーマ）
    
    条件:
    - ⭐ 星の塔: フォロワー0-10（誰も知らない新星）
    - 🌙 月の塔: フォロワー11-100（少数が注目）
    - ☀️ 太陽の塔: フォロワー101-1000（期待作）
    - 🌟 那由多の塔: フォロワー1001+（大注目）
    """
    if follower_count <= 10:
        return "星の塔"
    elif follower_count <= 100:
        return "月の塔"
    elif follower_count <= 1000:
        return "太陽の塔"
    else:
        return "那由多の塔"


def extract_preview_urls(steam_data: dict) -> dict:
    """
    ホバープレビュー用のURL抽出
    
    Returns:
        {
            "video_url": str or None,
            "video_thumbnail": str or None,
            "screenshots": [url, ...]
        }
    """
    video_url = None
    video_thumbnail = None
    screenshots = []
    
    # 動画（最初の1つ）- 新しいSteam API形式に対応
    movies = steam_data.get("movies", [])
    if movies:
        first_movie = movies[0]
        # 旧形式（webm）を優先
        webm = first_movie.get("webm", {})
        video_url = webm.get("480") or webm.get("max")
        
        # 新形式（HLS/DASH）にフォールバック
        if not video_url:
            # mp4形式を優先（最も互換性が高い）
            mp4 = first_movie.get("mp4", {})
            video_url = mp4.get("480") or mp4.get("max")
        
        # それでもない場合はHLSを使用（ブラウザサポートが必要）
        if not video_url:
            video_url = first_movie.get("hls_h264")
        
        video_thumbnail = first_movie.get("thumbnail")
    
    # スクリーンショット（最大5枚）
    ss_list = steam_data.get("screenshots", [])
    for ss in ss_list[:5]:
        screenshots.append(ss.get("path_thumbnail") or ss.get("path_full"))
    
    return {
        "video_url": video_url,
        "video_thumbnail": video_thumbnail,
        "screenshots": screenshots,
    }


# テスト用
if __name__ == "__main__":
    # Vampire Survivors (AppID: 1794680) でテスト
    test_id = 1794680
    print(f"Testing with AppID: {test_id}")
    
    steam = get_app_details(test_id)
    print(f"\n[Steam API]")
    print(f"  Name: {steam.get('name')}")
    print(f"  Japanese: {steam.get('is_japanese_supported')}")
    print(f"  Movies: {len(steam.get('movies', []))} found")
    print(f"  Screenshots: {len(steam.get('screenshots', []))} found")
    print(f"  Recommendations: {steam.get('recommendations')}")
    
    reviews = get_app_reviews_summary(test_id)
    print(f"\n[Reviews API]")
    print(f"  Total: {reviews.get('total_reviews')}")
    print(f"  Positive: {reviews.get('total_positive')}")
    print(f"  Score: {reviews.get('review_score_desc')}")
    
    label = calc_attention_label(reviews.get('total_reviews', 0), reviews.get('review_score_desc', ''))
    print(f"\n[Attention Label]: {label}")
