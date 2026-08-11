import os
import json
import urllib.parse
import pandas as pd
import gspread

# (前面的 ALL_STORES 保持不變)
# ...

def update_google_sheet():
    df = pd.DataFrame(ALL_STORES)
    
    # 照片公式
    df["photo"] = df["image_url"].apply(
        lambda url: f'=IMAGE("{url}")' if url else ""
    )
    
    # 建立試算表超連結與 Streamlit 用的純 URL
    df["map_url"] = df.apply(
        lambda row: f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(row['store_name'] + ' ' + row['address'])}",
        axis=1
    )
    df["search_url"] = df["store_name"].apply(
        lambda name: f"https://www.google.com/search?q={urllib.parse.quote(name)}"
    )

    df["map_link"] = df["map_url"].apply(lambda url: f'=HYPERLINK("{url}", "📍 開啟地圖")')
    df["web_search"] = df["search_url"].apply(lambda url: f'=HYPERLINK("{url}", "🔍 搜尋網頁")')
    
    cols = ["store_id", "store_name", "photo", "map_link", "web_search", "map_url", "search_url", "country", "city", "address", "concept", "lat", "lng", "image_url"]
    df = df[cols]
    df["updated_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")

    print(f"🚀 正在寫入 {len(df)} 筆門市資料至 Google 試算表...")
    creds_json = os.environ.get("GOOGLE_CREDS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        gc = gspread.service_account_from_dict(creds_dict)
    else:
        gc = gspread.service_account(filename="google_creds.json")

    spreadsheet_id = os.environ.get("SPREADSHEET_ID")
    if spreadsheet_id:
        sh = gc.open_by_key(spreadsheet_id)
    else:
        sh = gc.open_by_key("YOUR_SPREADSHEET_ID")

    worksheet = sh.sheet1
    worksheet.clear()
    
    worksheet.update(
        [df.columns.values.tolist()] + df.values.tolist(),
        value_input_option="USER_ENTERED"
    )
    print("✅ 成功寫入資料！")

if __name__ == "__main__":
    update_google_sheet()
