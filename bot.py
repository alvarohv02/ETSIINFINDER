import discord
from discord.ext import commands, tasks
from discord.utils import get
import os
import sqlite3
import asyncio
from random import randint
from dotenv import load_dotenv
from typing import Dict, Any
import re
import uuid

load_dotenv()

MAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@alumnos\.upm\.es$'

bot = commands.Bot(command_prefix="!", intents=discord.Intents().all())



db : Dict[int, Dict[str, Any]] = {}

@bot.event
async def on_ready():
    print("Listo")
    await bot.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name="Siendo Programado 💻​"))
    for guild in bot.guilds:
        print(f"guild {guild}")
        print(f"guild_id: {guild.id}")
        for channel in guild.text_channels :
            print(f"channel {channel}")
            print(f"id : {channel.id}")
        print('Active in {}\nMember Count : {}'.format(guild.name, guild.member_count))

@bot.event
async def mail_message(message : discord.Message):
    if message.author == bot.user:
        return
    
    elif message.channel.id == int(os.environ("MAIL_ID")):
        db[message.author.id]["mail"] = message.content
        if re.match(MAIL_REGEX, message.content):
            channel = bot.get_channel(int(os.environ("ADMIN_CHANNEL_ID")))
            await channel.send(f"Un usuario no ha introducido un correo @alumnos.upm.es: {message.author.name}, ha introducido el correo: {message.content}")
        await message.delete()

@bot.event
async def hobbies_message(message : discord.Message):
    if message.author == bot.user:
        return
    
    elif message.channel.id == int(os.environ("HOBBIES_ID")):
        db[message.author.id]["hobbies"] = message.content
        await message.delete()
    
@bot.event
async def on_message_join(member : discord.Member):
    roles = [role.name for role in member.roles if role.name != "@everyone"]
    db[member.id]["roles"] = roles

'''
    # channel = bot.get_channel(int(os.environ["CHANNEL_ID"]))
    # await channel.send(embed=new_member(), view=UserGender())
    # await channel.send(embed=finding_with(), view=FindingGender())

def new_member() -> discord.Embed:
        new_embed = discord.Embed(title="Hola", color=discord.Color.random())
        # embeded_message.set_thumbnail(url=ctx.guild.icon) # Poner una imagen cuando la halla
        return new_embed

def finding_with():
    new_embed = discord.Embed(title="Adios", color=discord.Color.random())
    return new_embed

class UserGender(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    async def assign_role(self, interaction: discord.Interaction, gender: str):
        """Asigna el rol correspondiente al usuario."""
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(interaction.user.id)
        role = discord.utils.get(guild.roles, name=gender)

        if not role:
            await interaction.response.send_message("⚠️ No se encontró el rol en el servidor.", ephemeral=True)
            return
        
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ Has seleccionado: {role.name}. Se te ha asignado el rol.", ephemeral=True)
    
    async def disable_buttons(self, interaction: discord.Interaction):
        """Deshabilita los botones después de la selección del usuario."""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.message.edit(view=self)

    async def handle_selection(self, interaction: discord.Interaction, gender: str):
        """Maneja la selección del usuario y deshabilita los botones si ya eligió."""
        if interaction.user.id in selected_users:
            await interaction.response.send_message("❌ Ya has elegido un género y no puedes cambiarlo.", ephemeral=True)
        else:
            selected_users.add(interaction.user.id)
            await self.assign_role(interaction, gender)
            await self.disable_buttons(interaction)

    @discord.ui.button(label="Hombre", style=discord.ButtonStyle.primary, custom_id="male")
    async def male_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_selection(interaction, "Soy hombre")

    @discord.ui.button(label="Mujer", style=discord.ButtonStyle.danger, custom_id="female")
    async def female_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_selection(interaction, "Soy mujer")

    @discord.ui.button(label="Otro", style=discord.ButtonStyle.success, custom_id="other")
    async def non_binary_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_selection(interaction, "Soy otro")

class FindingGender(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    async def assign_role(self, interaction: discord.Interaction, gender: str):
        """Asigna el rol correspondiente al usuario."""
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(interaction.user.id)
        role = discord.utils.get(guild.roles, name=gender)

        if not role:
            await interaction.response.send_message("⚠️ No se encontró el rol en el servidor.", ephemeral=True)
            return
        
        await member.add_roles(role)
        await interaction.response.send_message(f"✅ Has seleccionado: {role.name}. Se te ha asignado el rol.", ephemeral=True)
    
    async def disable_buttons(self, interaction: discord.Interaction):
        """Deshabilita los botones después de la selección del usuario."""
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.message.edit(view=self)

    async def handle_selection(self, interaction: discord.Interaction, gender: str):
        """Maneja la selección del usuario y deshabilita los botones si ya eligió."""
        if interaction.user.id in finded_users:
            await interaction.response.send_message("❌ Ya has elegido lo que buscas y no puedes cambiarlo.", ephemeral=True)
        else:
            finded_users.add(interaction.user.id)
            await self.assign_role(interaction, gender)
            await self.disable_buttons(interaction)

    @discord.ui.button(label="Busco hombre", style=discord.ButtonStyle.primary, custom_id="find_male")
    async def male_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_selection(interaction, "Busco hombre")

    @discord.ui.button(label="Busco mujer", style=discord.ButtonStyle.danger, custom_id="find_female")
    async def female_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_selection(interaction, "Busco mujer")

    @discord.ui.button(label="Busco ambos", style=discord.ButtonStyle.success, custom_id="find_other")
    async def non_binary_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.handle_selection(interaction, "Busco ambos")
'''
async def main():
    async with bot:
        await bot.start(os.environ["TOKEN"])

asyncio.run(main())