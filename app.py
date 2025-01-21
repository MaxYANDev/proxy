from flask import Flask, Response
import requests
import time
import threading

app = Flask(__name__)

# 全局变量存储所有频道的 m3u8 URL
latest_m3u8_urls = {}

def fetch_m3u8_urls():
    global latest_m3u8_urls
    while True:
        try:
            # 调用 API 获取数据
            api_url = "https://mapi.dtradio.com.cn/api/v1/channel.php?"
            response = requests.get(api_url)
            data = response.json()

            # 提取所有频道的 m3u8 URL
            m3u8_urls = {channel["name"]: channel["m3u8"] for channel in data if "m3u8" in channel}
            latest_m3u8_urls = m3u8_urls
            print("Updated m3u8 URLs:", latest_m3u8_urls)
        except Exception as e:
            print("Error fetching m3u8 URLs:", e)

        # 每小时更新一次
        time.sleep(3600)

# 启动后台线程定期更新 m3u8 URL
update_thread = threading.Thread(target=fetch_m3u8_urls)
update_thread.daemon = True
update_thread.start()

@app.route("/playlist.m3u8", methods=["GET"])
def get_playlist():
    if latest_m3u8_urls:
        # 生成符合 TiviMate 标准的 .m3u8 文件
        m3u8_content = "#EXTM3U\n"
        for name, url in latest_m3u8_urls.items():
            # 添加分组信息
            m3u8_content += f'#EXTGRP:大同\n'
            # 添加频道信息（显示名称为 "大同"）
            m3u8_content += f'#EXTINF:-1 tvg-id="{name}" tvg-name="{name}", 大同\n'
            m3u8_content += f"{url}\n"
        return Response(m3u8_content, content_type="application/vnd.apple.mpegurl")
    else:
        return "m3u8 URLs not available", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)