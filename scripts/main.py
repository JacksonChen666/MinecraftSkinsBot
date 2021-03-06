import discord
from discord.ext import commands
import os
import io
import sys
import json
import shutil
from base64 import b64decode
import requests
from dotenv import load_dotenv

import cv2
import numpy as np

DEBUG = False
SIMULATE = False

userid_url = "https://api.mojang.com/users/profiles/minecraft/{username}"
userinfo_url = "https://sessionserver.mojang.com/session/minecraft/profile/{userid}"
avatar_url = "https://crafatar.com/avatars/{userid}"
body_url = "https://crafatar.com/renders/body/{userid}"

client = discord.Client()
bot = commands.Bot(command_prefix=">")
bot.remove_command("help")
username = ""

@bot.event
async def on_ready():
  print("We have logged in as {0.user}".format(bot))


@bot.command(pass_context = True)
async def help(ctx):
  embed = discord.Embed(title = "Help",
    colour = discord.Colour.green()
  )



  embed.add_field(name="skin",value= "Shows the skin of the specified player.",inline=False)

  embed.add_field(name="avatar",value= "Shows the avatar of the specified player.",inline=False)

  embed.add_field(name="body",value= "Shows the body of the specified player.",inline=False)

  embed.add_field(name="convert",value= "Creates a skin from the image you attach. (add the command in the comments of your image).",inline=False)

  embed.set_thumbnail(url= "https://i.ibb.co/vV5GXnT/logo.png")

  embed.set_footer(text = "Made with ❤️ by dextero")

  await ctx.channel.send(embed = embed)

@bot.command()
async def hi(ctx):
  await ctx.channel.send("Hello!")
  return

@bot.command()
async def showthecount(ctx):
  await ctx.channel.send(len(bot.guilds))
  return

@bot.command()
async def skin(ctx):
  command_list = ctx.message.content.split(" ")
  if len(command_list) < 2:
    await ctx.channel.send("Please enter a valid username")
    username = "123blank89"
    sys.exit(0)
  else:
    username = command_list[1]
  await ctx.channel.send(username)

  r = get_url(userid_url.format(username=username))
  if r.status_code != 200:
        await ctx.channel.send("Could not retrieve user ID for {username}".format(username=username))
        return
        
  if DEBUG:
      print("{0} {1}".format(r.status_code, userid_url.format(username=username)), file=sys.stderr)
  userid = r.json()['id']

  r = get_url(userinfo_url.format(userid=userid))
  if r.status_code != 200:
      fail("Failed to download user info for {username}".format(username=username),
             "{0} {1}".format(r.status_code, userinfo_url.format(userid=userid)))
  if DEBUG:
      print("{0} {1}".format(r.status_code, userinfo_url.format(userid=userid)), file=sys.stderr)
  userinfo = r.json()
  texture_info = find_texture_info(userinfo['properties'])
  if texture_info is None:
      fail("Failed to find texture info for {username}".format(username=username),
             userinfo)

  try:
     skin_url = texture_info['textures']['SKIN']['url']
  except:
     fail("Failed to find texture info for {username}".format(username=username),
             texture_info)
  r = get_url(skin_url, stream=True)  
  if r.status_code != 200:
      fail("Could not download skin for {username}".format(username=username),
             "{0} {1}".format(r.status_code, skin_url))
  if DEBUG:
      print("{0} {1}".format(r.status_code, skin_url), file=sys.stderr)

  with open("{username}.png".format(username=username), 'wb') as f:
    shutil.copyfileobj(r.raw, f)
  await ctx.channel.send(file=discord.File("{username}.png".format(username=username)))
  os.remove("{username}.png".format(username=username)) 


  return




@bot.command()
async def avatar(ctx):
  command_list = ctx.message.content.split(" ")
  if len(command_list) < 2:
    await ctx.channel.send("Please enter a valid username")
    username = "123blank89"
    sys.exit(0)
  else:
    username = command_list[1]
  await ctx.channel.send(username)

  r = get_url(userid_url.format(username=username))
  if r.status_code != 200:
        await ctx.channel.send("Could not retrieve user ID for {username}".format(username=username))
        return

  userid = r.json()['id']

  await ctx.channel.send(avatar_url.format(userid=userid))

  return









@bot.command()
async def body(ctx):
  command_list = ctx.message.content.split(" ")
  if len(command_list) < 2:
    await ctx.channel.send("Please enter a valid username")
    username = "123blank89"
    sys.exit(0)
  else:
    username = command_list[1]
  await ctx.channel.send(username)

  r = get_url(userid_url.format(username=username))
  if r.status_code != 200:
        await ctx.channel.send("Could not retrieve user ID for {username}".format(username=username))
        return

  userid = r.json()['id']

  await ctx.channel.send(body_url.format(userid=userid))




@bot.command()
async def convert(ctx):
  image_types = ["png", "jpeg", "jpg"]
  if len(ctx.message.attachments) == 0:
    await ctx.channel.send("No attachments")
    return
  if any(ctx.message.attachments[0].filename.lower().endswith(image) for image in image_types):
    await ctx.message.attachments[0].save(ctx.message.attachments[0].filename) #save attachment


    file_name = ctx.message.attachments[0].filename
    hex = "000000"
    base_image = cv2.imread(file_name)



    #new code from skin converter github


    b_channel, g_channel, r_channel = cv2.split(base_image)
    alpha_channel = np.ones(b_channel.shape, dtype=b_channel.dtype) * 255

    base_image = cv2.merge((b_channel, g_channel, r_channel, alpha_channel))

    (h1, w1) = base_image.shape[:2]

    r = 32 / float(h1)
    dim = (int(w1 * r), 32)

    fit_to_skin_height = cv2.resize(base_image, dim)

    (_, w2) = fit_to_skin_height.shape[:2]

    x1 = int(w2/2 - 8)
    x2 = int(w2/2 + 8)

    fit_to_skin_width = fit_to_skin_height[0:32, x1:x2]

# Grab components from skin
    skin_head = fit_to_skin_width[0:8, 4:12]
    skin_left_arm = fit_to_skin_width[8:20, 0:4]
    skin_right_arm = fit_to_skin_width[8:20, 12:]
    skin_body = fit_to_skin_width[8:20, 4:12]
    skin_left_leg = fit_to_skin_width[20:, 4:8]
    skin_right_leg = fit_to_skin_width[20:, 8:12]

# Generate a preview image
    skin_preview = np.zeros((32, 16, 4), np.uint8)

    skin_preview[0:8, 4:12] = skin_head
    skin_preview[8:20, 0:4] = skin_left_arm
    skin_preview[8:20, 12:] = skin_right_arm
    skin_preview[8:20, 4:12] = skin_body
    skin_preview[20:, 4:8] = skin_left_leg
    skin_preview[20:, 8:12] = skin_right_leg

    # Generate a preview of the skin
    print('Saved preview as ' + 'skin_preview_' + file_name.split('.')[0] + '.png')
    cv2.imwrite('skins/skin_preview_' + file_name.split('.')[0] + '.png', skin_preview)

    skin_image = np.zeros((64, 64, 4), np.uint8)

    # Draw image on front of skin
    # (8, 8, 16, 16)
    skin_image[8:16, 8:16] = skin_head
    # (20, 20, 28, 32)
    skin_image[20:32, 20:28] = skin_body
    # (36, 52, 40, 64)
    skin_image[52:64, 36:40] = skin_right_arm
    # (44, 20, 48, 32)
    skin_image[20:32, 44:48] = skin_left_arm
    # (20, 52, 24, 64)
    skin_image[52:64, 20:24] = skin_right_leg
    # (4, 20, 8, 32)
    skin_image[20:32, 4:8] = skin_left_leg

    # Convert hex color for background to bgr
    hlen = len(hex)
    rgb = tuple(int(hex[i:i+int(hlen/3)], 16) for i in range(0, hlen, int(hlen/3)))

    bgr = (rgb[2], rgb[1], rgb[0], 255)

    # Draw rest of skin

    # (8, 0, 16, 8)
    cv2.rectangle(skin_image, (8, 0), (15, 7), bgr, -1)
    # (16, 0, 24, 8)
    cv2.rectangle(skin_image, (16, 0), (23, 7), bgr, -1)
    # (0, 8, 8, 16)
    cv2.rectangle(skin_image, (0, 8), (7, 15), bgr, -1)
    # (16, 8, 24, 16)
    cv2.rectangle(skin_image, (16, 8), (23, 15), bgr, -1)
    # (24, 8, 32, 16)
    cv2.rectangle(skin_image, (24, 8), (31, 15), bgr, -1)
    # (4, 16, 8, 20)
    cv2.rectangle(skin_image, (4, 16), (7, 19), bgr, -1)
    # (8, 16, 12, 20)
    cv2.rectangle(skin_image, (8, 16), (11, 19), bgr, -1)
    # (0, 20, 4, 32)
    cv2.rectangle(skin_image, (0, 20), (3, 31), bgr, -1)
    # 8, 20, 12, 32)
    cv2.rectangle(skin_image, (8, 20), (11, 31), bgr, -1)
    # (12, 20, 16, 32)
    cv2.rectangle(skin_image, (12, 20), (15, 31), bgr, -1)
    # (20, 16, 28, 20)
    cv2.rectangle(skin_image, (20, 16), (27, 19), bgr, -1)
    # (28, 16, 36, 20)
    cv2.rectangle(skin_image, (28, 16), (35, 19), bgr, -1)
    # (16, 20, 20, 32)
    cv2.rectangle(skin_image, (16, 20), (19, 31), bgr, -1)
    # (28, 20, 32, 32)
    cv2.rectangle(skin_image, (28, 20), (31, 31), bgr, -1)
    # (32, 20, 40, 32)
    cv2.rectangle(skin_image, (32, 20), (39, 31), bgr, -1)
    # (44, 16, 48, 20)
    cv2.rectangle(skin_image, (44, 16), (47, 19), bgr, -1)
    # (48, 16, 52, 20)
    cv2.rectangle(skin_image, (48, 16), (51, 19), bgr, -1)
    # (40, 20, 44, 32)
    cv2.rectangle(skin_image, (40, 20), (43, 31), bgr, -1)
    # (48, 20, 52, 32)
    cv2.rectangle(skin_image, (48, 20), (51, 31), bgr, -1)
    # (52, 20, 56, 32)
    cv2.rectangle(skin_image, (52, 20), (55, 31), bgr, -1)
    # (20, 48, 24, 52)
    cv2.rectangle(skin_image, (20, 48), (23, 51), bgr, -1)
    # (24, 48, 28, 52)
    cv2.rectangle(skin_image, (24, 48), (27, 51), bgr, -1)
    # (16, 52, 20, 64)
    cv2.rectangle(skin_image, (16, 52), (19, 63), bgr, -1)
    # (24, 52, 28, 64)
    cv2.rectangle(skin_image, (24, 52), (27, 63), bgr, -1)
    # (28, 52, 32, 64)
    cv2.rectangle(skin_image, (28, 52), (31, 63), bgr, -1)
    # (36, 48, 40, 52)
    cv2.rectangle(skin_image, (36, 48), (39, 51), bgr, -1)
    # (40, 48, 44, 52)
    cv2.rectangle(skin_image, (40, 48), (43, 51), bgr, -1)
    # (32, 52, 36, 64)
    cv2.rectangle(skin_image, (32, 52), (35, 63), bgr, -1)
    # (40, 52, 44, 64)
    cv2.rectangle(skin_image, (40, 52), (43, 63), bgr, -1)
    # (44, 52, 48, 64)
    cv2.rectangle(skin_image, (44, 52), (47, 63), bgr, -1)

    # Output final skin
    print('Saved skin as ' + 'skin_' + file_name.split('.')[0] + '.png')
    cv2.imwrite('skin_' + file_name.split('.')[0] + '.png', skin_image)

    await ctx.channel.send(file=discord.File('skin_'+file_name))
    os.remove('skin_'+file_name) 
    os.remove(file_name)

    return

  

  


@client.event
async def on_message(message):
  if message.author == client.user:
    return



class SimulatedResponse(object):
    def __init__(self, content, is_json, raw=None):
        self.content = content
        self.is_json = is_json
        self.status_code = 200
        self.raw = raw

    def json(self):
        if self.is_json:
            return json.loads(self.content)
        return None

def fail(msg, verbose_msg):
    print(msg, file=sys.stderr)

    if DEBUG:
        print(verbose_msg, file=sys.stderr)
    sys.exit(1)

def find_texture_info(properties):
    for prop in properties:
        if prop['name'] == 'textures':
            return json.loads(b64decode(prop['value'], validate=True).decode('utf-8'))
    return None

def get_url(url, **kwargs):
    if SIMULATE:
        content = None
        is_json = False
        raw = None
        if url.startswith('https://api.mojang.com/users/profiles/minecraft/'):
            with open('simulated_userid_response.json', 'r') as f:
                content = f.read()
            is_json = True
        elif url.startswith('https://sessionserver.mojang.com/session/minecraft/profile/'):
            with open('simulated_userinfo_response.json', 'r') as f:
                content = f.read()
            is_json = True
        else:
            with open('simulated_skin_response.png', 'rb') as f:
                content = f.read()
            is_json = False
            raw = io.BytesIO(content)
        return SimulatedResponse(content, is_json, raw)
    else:
        return requests.get(url, **kwargs)

#get the token from .env file and run the bot
load_dotenv()
bot.run(os.getenv('TOKEN'))