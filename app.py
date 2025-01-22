from flask import Flask, request, Response, redirect
import requests
import time
import threading
import logging
import os

app = Flask(__name__)

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("proxy.log"),  # 输出到文件
        logging.StreamHandler()  # 输出到控制台
    ]
)

# 全局变量存储所有频道的 m3u8 地址和更新时间
latest_m3u8_urls = {}
last_update_time = 0
CACHE_EXPIRY = 3600  # 缓存过期时间（秒）
LOCAL_IP = "192.168.1.23"  # 本地 IP 地址

def fetch_latest_urls():
    global latest_m3u8_urls, last_update_time
    try:
        # 调用 API 获取数据
        api_url = "https://mapi.dtradio.com.cn/api/v1/channel.php?"
        logging.debug("Fetching data from API: %s", api_url)
        response = requests.get(api_url)
        logging.debug("API response: %s", response.text)
        data = response.json()

        # 提取所有频道的 m3u8 URL
        m3u8_urls = {}
        for channel in data:
            if "m3u8" in channel:
                # 直接使用 API 返回的 m3u8 URL
                m3u8_urls[channel["name"]] = channel["m3u8"]

        latest_m3u8_urls = m3u8_urls
        last_update_time = time.time()
        logging.info("Updated latest m3u8 URLs: %s", latest_m3u8_urls)
    except Exception as e:
        logging.error("Error fetching latest m3u8 URLs: %s", e)

@app.route("/playlist.m3u8", methods=["GET"])
def get_playlist():
    global latest_m3u8_urls, last_update_time

    # 检查缓存是否过期
    if time.time() - last_update_time > CACHE_EXPIRY:
        logging.info("Cache expired, fetching latest m3u8 URLs...")
        fetch_latest_urls()

    # 生成总的 IPTV 列表
    m3u8_content = "#EXTM3U\n"
    for channel_name in latest_m3u8_urls:
        # 使用 LOCAL_IP 和 LOCAL_PORT 构建本地固定地址
        local_url = f"http://{LOCAL_IP}/{channel_name}.m3u8"
        m3u8_content += f'#EXTINF:-1 tvg-id="{channel_name}" tvg-name="{channel_name}", 大同\n'
        m3u8_content += f"{local_url}\n"

    logging.debug("Generated .m3u8 file content:\n%s", m3u8_content)
    return Response(m3u8_content, content_type="application/vnd.apple.mpegurl")

@app.route("/<channel_name>.m3u8", methods=["GET"])
def proxy_m3u8(channel_name):
    global latest_m3u8_urls, last_update_time

    # 检查缓存是否过期
    if time.time() - last_update_time > CACHE_EXPIRY:
        logging.info("Cache expired, fetching latest m3u8 URLs...")
        fetch_latest_urls()

    # 获取对应频道的 m3u8 URL
    if channel_name in latest_m3u8_urls:
        m3u8_url = latest_m3u8_urls[channel_name]
        logging.debug("Redirecting request for %s to: %s", channel_name, m3u8_url)
        return redirect(m3u8_url)
    else:
        return f"Channel {channel_name} not found", 404

if __name__ == "__main__":
    # 启动时先获取一次直播地址
    fetch_latest_urls()
    app.run(host="0.0.0.0", port=8080, debug=True)  # 启用调试模式