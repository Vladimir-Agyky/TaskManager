import discord
import psutil
import os
import asyncio
import time
import json
import datetime
import pytz

with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = config["TOKEN"]
SYSTEM_CHANNEL_ID = config["SYSTEM_CHANNEL_ID"]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
last_system_embed = None

async def send_system_stats():
    await client.wait_until_ready()
    system_channel = client.get_channel(SYSTEM_CHANNEL_ID)
    
    if not system_channel:
        print("채널을 찾을 수 없습니다. 채널 ID를 확인하세요.")
        return

    global last_system_embed
    prev_net_io = psutil.net_io_counters()

    while not client.is_closed():
        await asyncio.sleep(5)  #Updates every 5 seconds

        net_io = psutil.net_io_counters()
        sent_gb = net_io.bytes_sent / (1024 ** 3)
        recv_gb = net_io.bytes_recv / (1024 ** 3)

        sent_diff_mb = (net_io.bytes_sent - prev_net_io.bytes_sent) / (1024 ** 2)
        recv_diff_mb = (net_io.bytes_recv - prev_net_io.bytes_recv) / (1024 ** 2)
        prev_net_io = net_io

        ram = psutil.virtual_memory()
        ram_used_gb = ram.used / (1024 ** 3)

        cpu_usage = psutil.cpu_percent(interval=1)

        try:
            temp = os.popen("vcgencmd measure_temp").readline()
            cpu_temp = float(temp.replace("temp=", "").replace("'C\n", ""))
        except:
            cpu_temp = "N/A"


        uptime_seconds = int(time.time() - psutil.boot_time())
        uptime_days = uptime_seconds // (24 * 3600)
        uptime_hours = (uptime_seconds % (24 * 3600)) // 3600
        uptime_minutes = (uptime_seconds % 3600) // 60
        uptime_secs = uptime_seconds % 60
        uptime_str = f"{uptime_days}일 {uptime_hours}시간 {uptime_minutes}분 {uptime_secs}초"

        kst = pytz.timezone("Asia/Seoul")
        current_time_kst = datetime.datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")

        system_embed = discord.Embed(title="📊 Real-Time Server Status", color=discord.Color.blue())
        system_embed.add_field(name="📡 Total Network Usage", value=f"🔽 Recieved : {recv_gb:.2f} GB\n🔼 Sent : {sent_gb:.2f} GB", inline=False)
        system_embed.add_field(name="🚀 Network Speed Now", value=f"🔽 Download : {recv_diff_mb:.1f} MB/s\n🔼 Upload : {sent_diff_mb:.1f} MB/s", inline=False)
        system_embed.add_field(name="💾 Ram Usage", value=f"{ram_used_gb:.2f}GB", inline=True)
        system_embed.add_field(name="🖥️ CPU Usage", value=f"{cpu_usage:.2f}%", inline=True)
        system_embed.add_field(name="🌡️ CPU Temp", value=f"{cpu_temp}°C", inline=True)
        system_embed.add_field(name="⏳ Uptime", value=uptime_str, inline=False)
        system_embed.set_footer(text=f"측정된 시각 (KST) {current_time_kst}")

        if last_system_embed:
            try:
                await last_system_embed.edit(embed=system_embed)
            except Exception as e:
                print(f"메시지 수정 실패: {e}")
                try:
                    await last_system_embed.delete()  # ✅ 이전 메시지 삭제
                except Exception as del_err:
                    print(f"이전 메시지 삭제 실패: {del_err}")
                last_system_embed = await system_channel.send(embed=system_embed)
        else:
            last_system_embed = await system_channel.send(embed=system_embed)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(send_system_stats())

client.run(TOKEN)