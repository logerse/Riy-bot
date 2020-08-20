import discord
import json
import requests
import asyncio
from discord.ext import commands
import sqlite3
import datetime
import random
import secret

TOKEN = secret.TOKEN
bot = commands.Bot(command_prefix='.')
bot.remove_command('help')

connection = sqlite3.connect('serv')
cursor = connection.cursor()

flag = 0

@bot.event
async def on_ready():
	await bot.change_presence(status = discord.Status.online, activity = discord.Game('Размышление о мире') )

	cursor.execute("""CREATE TABLE IF NOT EXISTS users (
		name TEXT,
		id INT,
		cash BIGINT,
		rep INT,
		lvl INT,
		server_id INT,
		xp INT,
                time_ INT
		)""")

	cursor.execute("""CREATE TABLE IF NOT EXISTS shop (
		role_id INT,
		id INT,
		cost BIGINT
		)""")
	connection.commit()

	for guild in bot.guilds:
		for member in guild.members:
			if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}") .fetchone() is None:
				cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0,0,1, {guild.id}, 0, 0)")
			else:
				pass

connection.commit()
print ('Успешно')

@bot.event
async def on_member_join(member):
	if cursor.execute(f"SELECT id FROM users WHERE id = {member.id}") .fetchone() is None:
		cursor.execute(f"INSERT INTO users VALUES ('{member}', {member.id}, 0,0,1, {member.guild.id},0, 0)")
	connection.commit()
	pass

@bot.command(aliases = ['balance', 'cash', 'bal', '$'])	
async def __balance(ctx, member: discord.Member = None):
	if member is None:
		await ctx.send(embed = discord.Embed(color = 0xff8888, title = 'Кошелек',
			description = f"""Сердец в кошельке **{ctx.author}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} :heart:**"""
			))
	else:
		await ctx.send(embed = discord.Embed(
			description = f"""Сердец в кошельке **{member}** составляет **{cursor.execute("SELECT cash FROM users WHERE id = {}".format(member.id)) .fetchone()[0]} :heart:**"""
			))

@bot.command (aliases = ['give', 'award'])
async def __award (ctx, member: discord.Member = None, amount: int = None):
	if member is None:
		await ctx.send(embed =discord.Embed(color = 0xff0000,title = 'Ошибка!', description = f"**{ctx.author}**, Укажите пользователя, которму нужно помочь с сердечками"))
	else:
		if amount is None:
			await ctx.send(embed =discord.Embed(color = 0xff0000,title = 'Ошибка!', description =f"**{ctx.author}**, Укажите кол-во сердечек, которое желаете начислить"))
		elif amount < 1 : 
			await ctx.send(embed =discord.Embed(color = 0xff0000,title = 'Ошибка!', description =f"**{ctx.author}**, Укажите больше 1 сердечка :heart:"))
		else:
			cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(amount, member.id))
		connection.commit()
	await ctx.message.add_reaction('✔')
pass

@bot.command(aliases = ['take'])
async def __take (ctx, member: discord.Member = None, amount = None):
	if member is None:
		await ctx.send(embed =discord.Embed(color = 0xff0000,title = 'Ошибка!', description = f"**{ctx.author}**, Укажите пользователя, у которого нужно забрать сердечки"))
	else:
		if amount is None:
			await ctx.send(embed =discord.Embed(color = 0xff0000,title = 'Ошибка!', description =f"**{ctx.author}**, Укажите кол-во сердечек, которое желаете отнять"))
		elif amount == 'all':
			cursor.execute("UPDATE users SET cash = {} WHERE id = {}".format(0, member.id))
			connection.commit()

			await ctx.message.add_reaction('✔')	
		elif int(amount) < 1: 
			await ctx.send(embed =discord.Embed(color = 0xff0000,title = 'Ошибка!', description =f"**{ctx.author}**, Укажите больше 1 сердечка :heart:"))
		else:
			cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(int(amount), member.id))
		connection.commit()

	await ctx.message.add_reaction('✔')	
pass

@bot.command(aliases = ['add-shop'])
async def __add_shop(ctx, role: discord.Role = None, cost: int = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль, которую вы желаете внести в магазин")
	else:
		if cost is None:
			await ctx.send(f"**{ctx.author}**, укажите стоимость для данной роли")
		elif cost < 1:
			await ctx.send(f"**{ctx.author}**, стоимость роли не может быть слишком маленькой")
		else:
			cursor.execute("INSERT INTO shop VALUES ({}, {}, {})".format(role.id, ctx.guild.id, cost))
			connection.commit()

			await ctx.message.add_reaction('✔')

@bot.command(aliases = ['remove-shop'])
async def __remove_shop(ctx, role: discord.Role = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль, которую хотите удалить из магазига")
	else:
		cursor.execute("DELETE FROM shop WHERE role_id = {}".format(role.id))
		connection.commit()

		await ctx.message.add_reaction('✔')

@bot.command(aliases = ['shop'])
async def _shop(ctx):
	embed = discord.Embed(title='Магазин ролей - крутышек')

	for row in cursor.execute("SELECT role_id, cost FROM shop WHERE id = {}".format(ctx.guild.id)):
		if ctx.guild.get_role(row[0]) != None:
			embed.add_field(
				name = f"Cтоимость {row[1]} :heart:",
				value = f"Вы получаете роль {ctx.guild.get_role(row[0]).mention}",
				inline = False
				)
		else:
			pass

	await ctx.send(embed = embed)		

@bot.command(aliases= ['buy', 'role-buy'])
async def __buy(ctx, role: discord.Role = None):
	if role is None:
		await ctx.send(f"**{ctx.author}**, укажите роль, которую хотите получить")
	else:
		if role in ctx.author.roles:
			await ctx.send(f"**{ctx.author}**, у Вас уже имеется данная роль!")
		elif cursor.execute("SELECT cost FROM shop WHERE role_id = {0}".format(role.id)).fetchone()[0] > cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]:
			await ctx.send(f"**{ctx.author}**, у Вас недостаточно сердечек для совершения покупки")
		else:
			await ctx.author.add_roles(role)
			cursor.execute("UPDATE users SET cash = cash - {0} WHERE id = {1}".format(cursor.execute("SELECT cost FROM shop WHERE role_id = {0}".format(role.id)).fetchone()[0], ctx.author.id))
			await ctx.message.add_reaction('✔')

@bot.command(aliases = ['rep', '+rep'])
async def __rep(ctx, member: discord.Member = None):
	if member is None:
		await ctx.send(f"**{ctx.author}**, укажите участника сервера")
	else:
		if member.id == ctx.author.id:
			await ctx.send(f"**{ctx.author}**, вы не можете указать самого себя")
		else:
			cursor.execute("UPDATE users SET rep = rep + {} WHERE id = {}".format(1, member.id))
			connection.commit()
			await ctx.message.add_reaction('✔')

@bot.command(aliases= ['lb'])
async def __leaderboard(ctx):
	embed = discord.Embed (color = 0xff3254, title = 'Топ 10')
	counter = 0

	for row in cursor.execute("SELECT name, cash FROM users WHERE server_id = {} ORDER BY cash DESC LIMIT 10".format(ctx.guild.id)):
		counter += 1
		embed.add_field(
		name = f'# {counter} место | `{row [0]}`', 
		value = f'Баланс: {row [1]} :heart:',
		inline = False,
	)
	await ctx.send(embed = embed)

@bot.command(aliases= ['lbxp'])
async def __leaderboardxp(ctx):
	embed = discord.Embed (color = 0xff3254, title = 'Топ 10')
	counter = 0

	for row in cursor.execute("SELECT name, xp FROM users WHERE server_id = {} ORDER BY xp DESC LIMIT 10".format(ctx.guild.id)):
		counter += 1
		embed.add_field(
		name = f'# {counter} место | `{row [0]}`', 
		value = f'Опыта: {row [1]} ',
		inline = False,
	)
	await ctx.send(embed = embed)

@bot.command(aliases= ['lblvl'])
async def __leaderboardlvl(ctx):
	embed = discord.Embed (color = 0xff3254, title = 'Топ 10')
	counter = 0

	for row in cursor.execute("SELECT name, lvl FROM users WHERE server_id = {} ORDER BY lvl DESC LIMIT 10".format(ctx.guild.id)):
		counter += 1
		embed.add_field(
		name = f'# {counter} место | `{row [0]}`', 
		value = f'Уровень: {row [1]}',
		inline = False,
	)
	await ctx.send(embed = embed)

@bot.command (aliases =['timely'])
async def __timely (ctx):
	global flag
	if flag: return
	flag = 1
	if datetime.datetime.now() >= getTime(ctx.author.id):
		await ctx.send(embed =discord.Embed(color = 0xff1220,title = 'Награда', description =f"**{ctx.author}**, Вы получили награду :heart:"))
		cursor.execute("UPDATE users SET cash = cash + 1000 WHERE id = {}".format(ctx.author.id))
		connection.commit()
		await ctx.message.add_reaction('✔')
		setTime(ctx.author.id, datetime.datetime.now() + datetime.timedelta(minutes=11))
	else:
		def formatTime(totalSeconds : int):
			return {'hours': str(int(totalSeconds // 3600)).zfill(2),
					'minutes': str(int((totalSeconds % 3600) // 60)).zfill(2),
					'seconds': str(int((totalSeconds % 60)//1)).zfill(2)}
		timeLeft = getTime(ctx.author.id) - datetime.datetime.now()
		timeLeft = formatTime(timeLeft.total_seconds())
		print(timeLeft.keys())
		await ctx.send(embed =discord.Embed(color = 0xff1220,title = 'Награда', description =f"**{ctx.author}**, до новых сердец осталось{timeLeft['hours']}:{timeLeft['minutes']}:{timeLeft['seconds']} :heart:"))
		await ctx.message.add_reaction('❌')
	flag = 0
@bot.event
async def on_message(message):

    if bot.user.id != message.author.id and len(message.content) > 10:#за каждое сообщение длиной > 10 символов...
        for row in cursor.execute("SELECT xp,lvl,cash FROM users where id={}".format(message.author.id)):
            expi=row[0]+random.randint(30, 40)#к опыту добавляется случайное число
            cursor.execute("UPDATE users SET xp={} where id={}".format(expi, message.author.id))
            lvch=expi/(row[1]*100)
            print(int(lvch))
            lv=int(lvch)
            if row[1] < lv:#если текущий уровень меньше уровня, который был рассчитан формулой выше,...
                await message.channel.send(f" Новый уровень")#то появляется уведомление...
                cursor.execute("UPDATE users SET lvl={},cash = cash + 333 where id={}".format(lv, message.author.id))#и участник получает деньги
    await bot.process_commands(message)#Далее это будет необходимо для ctx команд
    connection.commit()

@bot.command (aliases =['lvl'])
async def __lvl (ctx, member: discord.Member = None):
	if member is None:
		await ctx.send(embed = discord.Embed(color = 0xaa8888, title = 'Левель',
			description = f"""Уровень игрока: **{ctx.author}** составляет **{cursor.execute("SELECT lvl FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]}**"""
			))
	else:
		await ctx.send(embed = discord.Embed(
			description = f"""Уровень игрока: **{member}** составляет **{cursor.execute("SELECT lvl FROM users WHERE id = {}".format(member.id)) .fetchone()[0]} :heart:**"""
			))

@bot.command (aliases =['xp'])
async def __xp (ctx, member: discord.Member = None):
	if member is None:
		await ctx.send(embed = discord.Embed(color = 0xaa8888, title = 'Левель',
			description = f"""Игрок: **{ctx.author}** имеет **{cursor.execute("SELECT xp FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]} опыта :ppp: **"""
			))
	else:
		await ctx.send(embed = discord.Embed(
			description = f"""Игрок: **{member}** имеет **{cursor.execute("SELECT xp FROM users WHERE id = {}".format(member.id)).fetchone()[0]} опыта:watermelon: **"""
			))
@bot.command(aliases = ['help'])
async def __help(ctx):
	await ctx.send(embed = discord.Embed(color = 0xba2242, title = 'ДОСТУПНЫЕ КОМАНДЫ',
		description = f"""
		===================================================
		!$                    ➤ Узнать баланс пользователя			     
		!shop                 ➤ Магазин ролей                      
		!buy [Укажите роль]   ➤ Покупка роли                   
		!timely               ➤ Награда раз в 11 минут                       
		!bf [t or h] [сумма]  ➤ Рулетка
		===================================================
		 """,
		))

random.seed(int(datetime.datetime.now().timestamp()))
@bot.command(aliases= ['bf'])
async def __casino(ctx, playerChoice, bet = None):
	var = ["t", "h"]
	if playerChoice not in var:
		await ctx.send(f"Ошибка")
		return
	if bet == 'all':
		cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id))
		bet = int(cursor.fetchone()[0])
	elif not bet:
		await ctx.send(f"Ваша ставка сыграет по дефолту(1% от вашего банка.") 
		cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id))
		bet = int(cursor.fetchone()[0] * 0.01) 
	elif int(bet) < 0:
		await ctx.send(f"Ай-ай-ай, нельзя использовать отрицательные числа.") 
		return
	if int(bet) > int(cursor.execute("SELECT cash FROM users WHERE id = {}".format(ctx.author.id)).fetchone()[0]):
		await ctx.send(f"**{ctx.author}**, у Вас недостаточно сердечек для ставки")
		return
	result = random.choice(var)
	if playerChoice == result:
		await ctx.send(f"**{ctx.author}**, угадал! +{bet} сердечек")
		cursor.execute("UPDATE users SET cash = cash + {} WHERE id = {}".format(bet, ctx.author.id))
	else:
		await ctx.send(f"**{ctx.author}**, НЕ угадал! -{bet} сердечек")
		cursor.execute("UPDATE users SET cash = cash - {} WHERE id = {}".format(bet, ctx.author.id))

	connection.commit()

#random.seed(datetime.datetime.now().total_seconds())
#random.choice(["T", "H"])
#@bot.command(aliases= )


#------------------#
def getTime(usr_ID):
    cursor.execute("SELECT time FROM users WHERE id = {}".format(usr_ID))
    return datetime.datetime.fromtimestamp(int(cursor.fetchone()[0]))

def setTime(usr_ID, dt=datetime.datetime.now()):
    seconds = int(dt.timestamp())
    cursur.execute("UPDATE users SET time = {} WHERE id = {}".format(seconds, usr_ID))
    connection.commit()
#------------------#



bot.run(TOKEN)
