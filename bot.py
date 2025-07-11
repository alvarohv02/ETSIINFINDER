import discord
from discord.ext import commands
from discord.utils import get
import os
import asyncio
from dotenv import load_dotenv
import re
import aiosqlite

load_dotenv()

MAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@alumnos\.upm\.es$'

bot = commands.Bot(command_prefix="/", intents=discord.Intents().all())

class Finder(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Buscar Match", style=discord.ButtonStyle.green)
    async def find_match(self, interaction : discord.Interaction, button : discord.ui.Button):
            await make_match(interaction)

@bot.event
async def on_ready():
    print("Listo")
    await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="❤️ Haciendo match desde tiempos inmemorables ❤️"))
    canal_mensaje = bot.get_channel(int(os.getenv("FINDER_ID"))) or await bot.fetch_channel(int(os.getenv("FINDER_ID")))
    if canal_mensaje:
        await canal_mensaje.send(f"🔥 PULSA para entrar en la lista de MATCHES 🔥", view=Finder())
    for guild in bot.guilds:
        print(f"guild {guild}")
        print(f"guild_id: {guild.id}")
        for channel in guild.text_channels :
            print(f"channel {channel}")
            print(f"id : {channel.id}")
        print('Active in {}\nMember Count : {}'.format(guild.name, guild.member_count))
        try:
            synced = await bot.tree.sync()
            print(f"Comandos sincronizados: {len(synced)}")
        except Exception as e:
            print(f"Error al sincronizar comandos: {e}")

async def make_match(interaction : discord.Interaction):
    async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
        cursor = await db.execute("SELECT gender, looking FROM Users WHERE ID = ? AND ghost_ban = ?;", (interaction.user.id, 0))
        gend_look = await cursor.fetchone()
        await cursor.close()
        if gend_look[1] == "Ambos" and gend_look[0] != "No binario":
            cursor = await db.execute("SELECT ID FROM Users WHERE looking IN (?, ?)  AND match_made = ? AND ghost_ban = ?;", ("Ambos", gend_look[0], 0, 0))
        
        elif gend_look[0] == "No binario":
            if gend_look[1] == "Hombre":
                cursor = await db.execute("SELECT ID FROM Users WHERE looking = ? AND gender = ? AND match_made = ? AND ghost_ban = ?;", ("Ambos", "Hombre", 0, 0))
            elif gend_look[1] == "Mujer":
                cursor = await db.execute("SELECT ID FROM Users WHERE looking = ? AND gender = ? AND match_made = ? AND ghost_ban = ?;", ("Ambos", "Mujer", 0, 0))
            elif gend_look[1] == "Ambos":
                cursor = await db.execute("SELECT ID FROM Users WHERE looking = ?  AND match_made = ? AND ghost_ban = ?;", ("Ambos", 0, 0))
        
        else:
            cursor = await db.execute("SELECT ID FROM Users WHERE looking = ? AND gender = ? AND match_made = ? AND ghost_ban = ?;", (gend_look[0], gend_look[1], 0, 0))
        
        result = await cursor.fetchone()
        await cursor.close()
        
        if result:
            await db.execute("UPDATE Users SET match_made = ? WHERE ID = ?;", (1, interaction.user.id))
            await db.execute("UPDATE Users SET match_made = ? WHERE ID = ?;", (1, result[0]))
            await db.commit()
    
    if result:
        guild = interaction.guild
        user_1 = bot.get_user(interaction.user.id)
        user_2 = bot.get_user(result[0])
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me : discord.PermissionOverwrite(view_channel = True, send_messages = True),
            user_1 : discord.PermissionOverwrite(view_channel = True, send_messages = True),
            user_2 : discord.PermissionOverwrite(view_channel = True, send_messages = True)
        }
        
        channel = await guild.create_text_channel(
            name=f"private-{user_1.name}-{user_2.name}",
            overwrites=overwrites
        )
        
        async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
            cursor = await db.execute("SELECT hobbies FROM Users WHERE ID = ?;", (user_1.id,))
            hobbies_1 = await cursor.fetchone()
            await cursor.close()
            cursor = await db.execute("SELECT hobbies FROM Users WHERE ID = ?;", (user_2.id,))
            hobbies_2 = await cursor.fetchone()
            await cursor.close()
        
        await channel.send(f"{user_1.mention} y {user_2.mention}, se ha creado este canal porque habéis coincidido en lo que buscáis.\n{user_1.mention} tiene estas aficiones: {hobbies_1[0]} y {user_2.mention} tiene estas aficiones: {hobbies_2[0]}.")
        await channel.send(f"Ahora teneis tiempo para hablar y conoceros, este canal se quedará abierto 12h, si despues de eso quereis seguir hablando, hacedlo por dm (mensaje directo), si quereis cerrar esta conversación y seguir buscando match, podeis hacerlo con el comando '/next' (usandolo en este canal) si por el contrario, quereis cerrarlo y no volver a buscar, usad '/close' (también en este canal).")
        await channel.send(f"{user_1.mention} and {user_2.mention}, this channel has been created because you have agreed on what you are looking for.\n{user_1.mention} has these hobbies: {hobbies_1[0]} and {user_2.mention} has these hobbies: {hobbies_2[0]}.")
        await channel.send(f"Now you have time to talk and get to know each other, this channel will remain open for 12 hours, if after that you want to continue talking, do it by DM (direct message), if you want to close this conversation and continue looking for a match, you can do so with the command '/next' (using it in this channel) if on the contrary, you want to close it and not search again, use '/close' (also in this channel).")
        asyncio.create_task(close_channel_later(channel))
    
    else:
        await interaction.response.send_message(f"Has entrado en la lista para buscar match", ephemeral=True)
    
    
async def close_channel_later(channel):
    await asyncio.sleep(43200)
    if channel:
        await channel.delete()


@bot.event
async def on_message(message : discord.Message):
    if message.author == bot.user:
        return
    async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
        cursor = await db.execute("SELECT * FROM Users WHERE ID = ?", (message.author.id,))
        result = await cursor.fetchone()
        if result is None:
            await db.execute("INSERT INTO Users (ID, match_made, ghost_ban) VALUES (?, ?, ?)", (message.author.id, 0, 0))
            await db.commit()
    if message.channel.id == int(os.getenv("MAIL_ID")):
        if re.match(MAIL_REGEX, message.content) is None:
            await message.channel.send(f"❌ {message.author.mention}, el correo no es válido. Debe ser un correo @alumnos.upm.es.")
            channel = bot.get_channel(int(os.getenv("ADMIN_CHANNEL_ID"))) or await bot.fetch_channel(int(os.getenv("ADMIN_CHANNEL_ID")))
            await channel.send(f"⚠️ Un usuario no ha introducido un correo válido: {message.author.name} ingresó {message.content}")
            guild = bot.get_guild(int(os.getenv("GUILD_ID")))
            if guild:
                jefe_role = discord.utils.get(guild.roles, name="Mod")
                if jefe_role:
                    await channel.send(f"{jefe_role.mention}")
                    
            await message.delete()
        elif re.match(MAIL_REGEX, message.content):
            async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
                cursor = await db.execute("SELECT ID FROM Users WHERE ID = ?", (message.author.id,))
                exists = await cursor.fetchone()
                await cursor.close()

                if not exists:
                    await db.execute("INSERT INTO Users (ID, mail) VALUES (?, ?)", (message.author.id, message.content))
                else:
                    await db.execute("UPDATE Users SET mail = ? WHERE ID = ?", (message.content, message.author.id))
                    
                updates = []
                for role in message.author.roles:
                    if role.name in ["Mujer", "Hombre", "No binario"]:
                        updates.append(("UPDATE Users SET gender = ? WHERE ID = ?", (role.name, message.author.id)))
                    elif role.name == "Busco hombre":
                        updates.append(("UPDATE Users SET looking = ? WHERE ID = ?", ("Hombre", message.author.id)))
                    elif role.name == "Busco mujer":
                        updates.append(("UPDATE Users SET looking = ? WHERE ID = ?", ("Mujer", message.author.id)))
                    elif role.name == "Busco ambos":
                        updates.append(("UPDATE Users SET looking = ? WHERE ID = ?", ("Ambos", message.author.id)))
                        
                for query, params in updates:
                    await db.execute(query, params)
                    
                await db.commit()
                
                cursor = await db.execute("SELECT * FROM Users WHERE ID = ?", (message.author.id,))
                result = await cursor.fetchone()
                
            await message.channel.send(f"✅ {message.author.mention}, tu correo ha sido guardado.")
            await message.delete()

            async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
                cursor = await db.execute("SELECT hobbies, mail FROM Users WHERE ID = ?", (message.author.id,))
                result = await cursor.fetchone()
                await cursor.close()
                
            if result is not None:
                role = discord.utils.get(message.guild.roles, name="Verified")
                await message.author.add_roles(role)
    
    elif int(message.channel.id) == int(os.getenv("HOBBIES_ID")):
        async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
            await db.execute("UPDATE Users SET hobbies = ? WHERE ID = ?", (message.content.lower(), message.author.id))
            await db.commit()
            cursor = await db.execute("SELECT hobbies, mail FROM Users WHERE ID = ?", (message.author.id,))
            result = await cursor.fetchone()
            await cursor.close()
        if result is not None:
            role = discord.utils.get(message.guild.roles, name="Verified")
            await message.author.add_roles(role)
        await message.delete()
        
@bot.event
async def on_member_join(member : discord.Member):
    async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
        await db.execute(f"INSERT INTO Users (ID, match_made, ghost_ban) VALUES (?, ?, ?)", (member.id, 0, 0))
        await db.commit()
 
@bot.command(name="next")
async def next(ctx : commands.Context):
    channel = ctx.channel
    members = [member for member in channel.members if not member.guild_permissions.administrator and not member.bot]
    if len(members) == 2:
        async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
            await db.execute("UPDATE Users SET match_made = ? WHERE ID = ?;", (0, members[0].id))
            await db.execute("UPDATE Users SET match_made = ? WHERE ID = ?;", (0, members[1].id))
            await db.commit()
            
        await ctx.send(f"El canal será cerrado ya que {ctx.author.mention} ha utilizado /next")
        await ctx.channel.delete()

@bot.command(name = "close")
async def close(ctx : commands.Context):
    channel = ctx.channel
    members = [member for member in channel.members if not member.guild_permissions.administrator and not member.bot]
    if len(members) == 2:
        async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
            await db.execute("UPDATE Users SET match_made = ? WHERE ID = ?;", (0, members[0 if members[0].id != ctx.author.id else 1].id))
            await db.commit()
        await ctx.send(f"El canal será cerrado ya que {ctx.author.mention} ha utilizado /close")
        await ctx.channel.delete()

@bot.tree.command(name="admin")
@discord.app_commands.describe(user="El usuario obtiene permisos de administrador")
async def admin(interaction : discord.Interaction, user: discord.Member):
    if any(role.name == "jefasos" or role.name=="Mod" for role in interaction.user.roles):
        guild = bot.get_guild(int(os.getenv("GUILD_ID")))
        try:
            role = discord.utils.get(guild.roles, name="jefasos")
            await user.add_roles(role)
            await interaction.response.send_message(f"Has dado permisos de administrador a {user.name}")
        except Exception as e:
            await interaction.response.send_message(f"{e}")
    else:
        await interaction.response.send_message(f"El usuario {interaction.user.mention} no tiene permisos de administrador")

@bot.tree.command(name="ghostban")
@discord.app_commands.describe(user="El usuario al que quieres hacer 'ghostban'")
async def ghostban(interaction: discord.Interaction, user: discord.Member):
    if any(role.name == "jefasos" for role in interaction.user.roles):
        async with aiosqlite.connect(str(os.getenv("DB_DIR"))) as db:
            await db.execute("UPDATE Users SET ghost_ban = ? WHERE ID = ?", (1, user.id))
            await db.commit()
        await interaction.response.send_message(f"Has hecho 'ghostban' a {user.name}", emeral=True)
    else:
        await interaction.response.send_message("❌ No tienes permiso para usar este comando.", ephemeral=True)

async def main():
    async with bot:
        await bot.start(os.getenv("TOKEN"))
        
asyncio.run(main())