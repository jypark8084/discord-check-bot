import discord
from discord.ext import commands, tasks
from discord import ui
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import os

# Load .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
TARGET_CHANNEL_ID = 1373649734845075517

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree  # ✅ tree 선언 추가

# 시간 포맷 함수
def get_kst_time():
    now = datetime.now(timezone(timedelta(hours=9)))
    return now.strftime("%Y년 %m월 %d일 %H시 %M분 %S초")

# 전역 메시지 저장용
sent_message = None

# ✅ 버튼이 달린 View
class CheckView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="체크", style=discord.ButtonStyle.success)
    async def check_button(self, interaction: discord.Interaction, button: ui.Button):
        global sent_message
        if sent_message:
            now = get_kst_time()
            new_content = f"```실시간 체크중 ({now} 확인됨)```"
            await sent_message.edit(content=new_content, view=CheckView())
            await interaction.response.send_message(f"✅ 메시지를 갱신했어요! ({now})", ephemeral=True)
        else:
            await interaction.response.send_message("❌ 메시지를 찾을 수 없어요.", ephemeral=True)

# ✅ 봇이 켜졌을 때
@bot.event
async def on_ready():
    print(f"✅ 봇 로그인됨: {bot.user}")
    await start_heartbeat()
    await tree.sync()

# ✅ 최초 메시지 전송 및 루프 시작
async def start_heartbeat():
    global sent_message
    channel = bot.get_channel(TARGET_CHANNEL_ID)
    if not channel:
        print("❌ 채널을 찾을 수 없습니다.")
        return

    now = get_kst_time()
    view = CheckView()
    sent_message = await channel.send(f"```실시간 체크중 ({now} 확인됨)```", view=view)
    update_loop.start()

# ✅ 1분마다 메시지 갱신
@tasks.loop(minutes=1)
async def update_loop():
    global sent_message
    if sent_message:
        now = get_kst_time()
        try:
            await sent_message.edit(content=f"```실시간 체크중 ({now} 확인됨)```", view=CheckView())
        except discord.NotFound:
            print("❌ 메시지를 찾을 수 없습니다. 루프 중지.")
            update_loop.stop()

@tree.command(name="지우기", description="지정된 채널의 모든 메시지를 삭제합니다.")
async def clear_messages(interaction: discord.Interaction):
    if interaction.channel_id != TARGET_CHANNEL_ID:
        await interaction.response.send_message("❌ 이 명령어는 지정된 채널에서만 사용할 수 있습니다.", ephemeral=True)
        return

    channel = interaction.channel
    await interaction.response.defer(thinking=True)
    deleted = await channel.purge(limit=1000)
    await interaction.followup.send(f"🧹 {len(deleted)}개의 메시지를 삭제했습니다.")

bot.run(TOKEN)
