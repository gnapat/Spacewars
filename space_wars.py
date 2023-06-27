#!/usr/bin/env python3
"""
Game name:		Space Wars (change to cooler name)
Author:			Dan Petersson
Github link:	https://github.com/DanPetersson/SpaceWars

Description:
---------------------------------------------------------
- Survive as long as possible as shoot as many aliens as possible to get good score

---------------------------------------------------------
Python:			3.8 						
PyGame:			1.9.6

Revision updates:
---------------------------------------------------------

REV 05 Add Easy med Hard
Backlog_revision_history.txt

"""

import pygame
import random
import math
import os
import json
import time
import sqlite3
import threading
import statistics
from datetime import datetime
from high_scores import high_scores
import logging
import time
import joblib
import pandas as pd
from river import datasets, linear_model, metrics, cluster, utils
from river.metrics import MAE, RMSE
from river import preprocessing

from river import neighbors
import math

from river import evaluate
from river import linear_model
from river import metrics
from river import optim
from river import tree
from river import drift
from river import forest
from river import metrics
from river import ensemble


#import space_wars_settings as sws

# ------------------
# Netpie
# ------------------

import microgear.client as microgear
import logging
import time

score_list = []
publish_time = datetime.now()

appid = 'datastream'
gearkey = 'qY0dhxc3TAswzeC'
gearsecret = 'eNInuhdaicInPOJl0KfPrBJfS'
user_score_topic = '/user_score_topic'

microgear.create(gearkey, gearsecret, appid, {'debugmode': False})
microgear.setalias("tanapong")

def connection():
    logging.info("Now I am connected with netpie")

def subscription(topic, message):
	import ast
	global score_list

	try:
		if topic == f"/{appid}{user_score_topic}" and message:
			score = json.loads(ast.literal_eval(message).decode('utf-8'))
			score_list.append(score)
	except Exception:
		pass
	#logging.info(topic + " " + message)

def disconnect():
    logging.info("disconnected")

microgear.on_connect = connection
microgear.on_message = subscription
microgear.on_disconnect = disconnect
microgear.subscribe(user_score_topic)
microgear.connect(False)

### Analytic Model
dt_scaler = joblib.load('./model/scaler.bin')
decision_tree = joblib.load('./model/model.h5')
LABELS = {2: 'Hardcore Achiever', 3: 'Hardcore Killer', 1: 'Casual Achiever', 0: 'Casual Killer'}
LABELS_ONLINE = {1: 'Hardcore Achiever', 3: 'Hardcore Killer', 0: 'Casual Achiever', 2: 'Casual Killer'}

def prediction_user_type(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count):
	global A0, A1
	a0 = statistics.mean(A0) if len(A0) else 0
	a1 = statistics.mean(A1) if len(A1) else 0
	a2 = coin_count
	a3 = destroyed_enemy_count
	a4 = shots_count
	a5 = A4 - A3
	a6 = level
	a7 = keyX_pressed_count
	a8 = keyY_pressed_count
	a9 = respawn_enemy_count
	a10 = respawn_coin_count
	# a11 = a3/a9
	# a12 = a2/a10
	X = [[a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10]]

	X_scale = dt_scaler.transform(X)
	y = decision_tree.predict(X_scale)[0]
	return LABELS.get(y)

def prediction_user_type_ex(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count):
	global A0, A1
	a0 = statistics.mean(A0) if len(A0) else 0
	a1 = statistics.mean(A1) if len(A1) else 0
	a2 = coin_count
	a3 = destroyed_enemy_count
	a4 = shots_count
	a5 = A4 - A3
	a6 = level
	a7 = keyX_pressed_count
	a8 = keyY_pressed_count
	a9 = respawn_enemy_count
	a10 = respawn_coin_count
	# a11 = a3/a9
	# a12 = a2/a10
	X = [[a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10]]

	X_scale = dt_scaler.transform(X)
	y = decision_tree.predict(X_scale)[0]
	return y


# initialize pygame 
pygame.init()

# Initialize global fonts
font_huge	= pygame.font.Font('freesansbold.ttf', 128)
font_large	= pygame.font.Font('freesansbold.ttf', 64)
font_medium	= pygame.font.Font('freesansbold.ttf', 32)
font_small	= pygame.font.Font('freesansbold.ttf', 16)
font_tiny	= pygame.font.Font('freesansbold.ttf', 8)

# Initialize global Game Colors
black 			= (  0,   0,   0)
white 			= (255, 255, 255)

red 			= (200,   0,   0)
green 			= (  0, 200,   0)
blue 			= (  0,   0, 200)
yellow 			= (200, 200,   0)

light_red 		= (255,   0,   0)
Light_green 	= (  0, 255,   0)
light_blue 		= (  0,   0, 255)
light_yellow	= (255, 255,   0)


# ----------------------------
# 		Define Classes
# ----------------------------

class SpaceObject:

	def __init__(self, image, explosion_image, posX=0, posY=0, speedX = 0, speedY = 0, sizeX = 64, sizeY = 64, 
					state = 'show', sound = ' ', hit_points = 1):
		#self.namme	= name
		self.image  = image
		self.explosion_image = explosion_image 
		self.sizeX  = sizeX
		self.sizeY  = sizeY
		self.posX   = posX
		self.posY   = posY
		self.speedX = speedX
		self.speedY	= speedY
		self.state	= state		# 'hide', 'show'
		self.sound 	= sound
		self.explosion_counter = -1
		self.hit_points = hit_points

	def show(self):
		if self.state == 'show' and self.explosion_counter <= 0:
			screen.blit(self.image, (int(self.posX), int(self.posY)))
		elif self.explosion_counter > 0:
			screen.blit(self.explosion_image, (int(self.posX), int(self.posY)))
			
class SpaceShip(SpaceObject):
    
    # def __init__(self):
    #     super().__init__()

	def update_player_postion(self, screen_sizeX, screen_sizeY):

		# Update X position (update with min/max)
		self.posX += self.speedX
		if self.posX < 0:
			self.posX = 0
		elif self.posX > screen_sizeX-self.sizeX:
			self.posX = screen_sizeX-self.sizeX

		# Update Y position (update with min/max)
		self.posY += self.speedY
		if self.posY < 0:
			self.posY = 0
		elif self.posY > screen_sizeY-self.sizeY:
			self.posY = screen_sizeY-self.sizeY

		#print(f"x = {self.posX}, y = {self.posY}")
		return([self.posX,self.posY])


class SpaceEnemy(SpaceObject):

	def update_enemy_position(self, screen_sizeX, screen_sizeY):

		# Update X position
		self.posX += self.speedX

		# Update Y position
		self.posY += self.speedY


class SpaceCoin(SpaceObject):

	def update_coin_position(self, screen_sizeX, screen_sizeY):

		# Update X position
		self.posX += self.speedX

		# Update Y position
		self.posY += self.speedY


class Bullet(SpaceObject):

	def update_bullet_position(self, screen_sizeX, screen_sizeY):

		# Update X position
		self.posX += self.speedX

		# Update Y position, and change state if outside screen
		self.posY += self.speedY
		if self.posY < -self.sizeY:
			self.state = 'hide'


	def fire_bullet(self, player):

		self.posX = player.posX + player.sizeX/2 - self.sizeX/2
		self.posY = player.posY
		self.sound.play()
		self.state = 'show'

class SuperWeapon(SpaceObject):
		
	def update_superweapon_position(self, screen_sizeX, screen_sizeY):

		# Update X position
		self.posX += self.speedX

		# Update Y position
		self.posY += self.speedY



class Button:

	def __init__(self, centerX, centerY, width, hight, text='', color=yellow, color_hoover=light_yellow, 
		text_color=black, text_hoover=black, font=font_small):
		self.centerX 		= int(centerX)
		self.centerY		= int(centerY)
		self.width 			= int(width)
		self.hight 			= int(hight)
		self.X				= int(centerX - width/2)
		self.Y				= int(centerY - hight/2)

		self.text 			= text
		self.color 			= color
		self.color_hoover	= color_hoover
		self.text_color		= text_color
		self.text_hoover	= text_hoover
		self.font 			= font
		self.clicked		= False

	# internal only function ?
	def text_objects(text, font, color):
	    text_surface = font.render(text, True, color)
	    return text_surface, text_surface.get_rect()

	# internal only function ?
	def message_display_center(text, font, color, centerX, centerY):
	    text_surface, text_rectangle = text_objects(text, font, color)
	    text_rectangle.center = (centerX,centerY)
	    screen.blit(text_surface, text_rectangle)

	def show(self, mouse=(0,0)):
		if self.X < mouse[0] < self.X + self.width and self.Y < mouse[1] < self.Y + self.hight:
			pygame.draw.rect(screen, self.color_hoover, (self.X, self.Y, self.width, self.hight))
		else:
			pygame.draw.rect(screen, yellow, (self.X, self.Y, self.width, self.hight))
		message_display_center(self.text, self.font, black, self.centerX, self.centerY)

	def check_clicked(self, mouse, mouse_click):
		if self.X < mouse[0] < self.X + self.width and self.Y < mouse[1] < self.Y + self.hight and mouse_click[0] == 1:
			self.clicked = True
		else:
			self.clicked = False



# ----------------------------
# 		Define Procedures
# ----------------------------


def text_objects(text, font, color):
	# Mainly supporting for function message_dipslay
    text_surface = font.render(text, True, color)
    return text_surface, text_surface.get_rect()

def message_display_center(text, font, color, centerX, centerY):
    text_surface, text_rectangle = text_objects(text, font, color)
    text_rectangle.center = (centerX,centerY)
    screen.blit(text_surface, text_rectangle)

def message_display_left(text, font, color, leftX, centerY):
    text_surface, text_rectangle = text_objects(text, font, color)
    text_rectangle.midleft = (leftX, centerY)
    screen.blit(text_surface, text_rectangle)

def message_display_right(text, font, color, rightX, centerY):
    text_surface, text_rectangle = text_objects(text, font, color)
    text_rectangle.midright = (rightX, centerY)
    screen.blit(text_surface, text_rectangle)

def show_high_scores():

#	global db_connection

	high_scores_screen = True
	while high_scores_screen:

		screen.fill(background_color)
		screen.blit(background_image[0], (0,0))

		message_display_center('High Scores', font_large, yellow, int(screen_sizeX/2), int(screen_sizeY * 1/10))
		message_display_center('Press (D)elete or any other key to continue', font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *9/10))

		top_5 = high_scores.high_scores_top_list(db_connection)

		index = 0
		for entry in top_5:
			# timestamp, name, score, date
			index += 1
			message_display_left(str(entry[1]), font_medium, yellow, int(screen_sizeX * 1/8), int(screen_sizeY *(2+index)/10))
			message_display_right(str(entry[2]), font_medium, yellow, int(screen_sizeX * 2/4), int(screen_sizeY *(2+index)/10))
			message_display_center(str(entry[3]), font_medium, yellow, int(screen_sizeX * 3/4), int(screen_sizeY *(2+index)/10))


		for event in pygame.event.get():	
			if event.type == pygame.QUIT:
				# add even mouse click ?
				high_scores_screen = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_d:
					# Deletes high score db table and recreates empty one
					high_scores.high_scores_db_delete(db_connection)
					high_scores.high_scores_create_table(db_connection)
				else:
					high_scores_screen = False

		# Display intro screen
		pygame.display.update()


def menu():
	# into screen 
	
	intro_screen = True
	level_game = 0
	while intro_screen:

		screen.fill(background_color)
		screen.blit(background_image[0], (0,0))

		message_display_center('SPACE WARS', font_large, yellow, int(screen_sizeX/2), int(screen_sizeY/3))
		message_display_center('New Game (Y/N)', font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *3/5))

		# get mouse position
		mouse = pygame.mouse.get_pos()
		mouse_click = pygame.mouse.get_pressed()

		# Define and draw buttons
		button_width 	= 130
		button_hight 	= 50

		# Define and draw "Yes" button
		easy_button_X 	= int(screen_sizeX*1/6)
		easy_button_Y 	= 400
		easy_button 		= Button(easy_button_X, easy_button_Y, button_width, button_hight, 'Easy')
		easy_button.show(mouse)
		easy_button.check_clicked(mouse, mouse_click)

		med_button_X 	= int(screen_sizeX*2/6)
		med_button_Y 	= 400
		med_button 		= Button(med_button_X, med_button_Y, button_width, button_hight, 'Medium')
		med_button.show(mouse)
		med_button.check_clicked(mouse, mouse_click)

		hard_button_X 	= int(screen_sizeX*3/6)
		hard_button_Y 	= 400
		hard_button 		= Button(hard_button_X, hard_button_Y, button_width, button_hight, 'Hard')
		hard_button.show(mouse)
		hard_button.check_clicked(mouse, mouse_click)

		# Define and draw "No" button
		no_button_X 	= int(screen_sizeX*4/6)
		no_button_Y 	= hard_button_Y
		no_button  		= Button(no_button_X,  no_button_Y,  button_width, button_hight, 'No')
		no_button.show(mouse)
		no_button.check_clicked(mouse, mouse_click)

		# Define and draw "High Scores" (hs) button
		hs_button_X 	= int(screen_sizeX*5/6)
		hs_button_Y 	= hard_button_Y
		hs_button  		= Button(hs_button_X,  hs_button_Y,  button_width, button_hight, 'High Scores')
		hs_button.show(mouse)
		hs_button.check_clicked(mouse, mouse_click)

		if easy_button.clicked:
			level_game =1
			intro_screen = False
			quit_game = False
		if med_button.clicked:
			level_game =3
			intro_screen = False
			quit_game = False
		if hard_button.clicked:
			level_game =2
			intro_screen = False
			quit_game = False
		if no_button.clicked:
			intro_screen = False
			quit_game = True

		if hs_button.clicked:
			show_high_scores()

		for event in pygame.event.get():	
			if event.type == pygame.QUIT:
				intro_screen = False
				quit_game = True

		# if 'Y' or 'N' key is pressed
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_y or event.key == pygame.K_z or event.key == pygame.K_RETURN:
					intro_screen = False
					quit_game = False
				if event.key == pygame.K_n:
					intro_screen = False
					quit_game = True

		# Display intro screen
		pygame.display.update()

	return quit_game,level_game

def paused(screen_sizeX, screen_sizeY):

	largeText = pygame.font.SysFont("freesansbold",115)
	TextSurf, TextRect = text_objects("Paused", largeText)
	TextRect.center = ((screen_sizeX/2),(screen_sizeX/2))
	screen.blit(TextSurf, TextRect)

	pause = True
	while pause:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				quit()
			if event.type == pygame.KEYDOWN:
				# 'p' for unpause 
				if event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
					pause = False
		screen.blit(TextSurf, TextRect)
		pygame.display.update()

		

def respawn(enemy, level):

	
	enemy.explosion_counter = -1	
	enemy.posX 	= random.randint(0, screen_sizeX - enemy.sizeX) 
	enemy.posY 	= random.randint(-screen_sizeY, -100)
	if enemy.posX < screen_sizeX / 3:
		enemy.speedX = random.randint(0, 10) / 10 * enemy.speedY
	elif enemy.posX > screen_sizeX * 2 / 3:
		enemy.speedX = random.randint(-10, 0) / 10 * enemy.speedY
	else:
		enemy.speedX = random.randint(-5, 5) / 10 * enemy.speedY

	#print(f"-----> respawn enemyX={enemy.posX}, enemyY={enemy.posY}")
	
#	enemy.speedY = level

def respawn2(enemy,x, level,glevel):

	
	enemy.explosion_counter = -1
	if glevel ==2:
		enemy.posX 	= random.randint(0, screen_sizeX - enemy.sizeX) 
	elif glevel == 3:
		enemy.posX 	= x #random.randint(0, screen_sizeX - enemy.sizeX) 

	enemy.posY 	= random.randint(-screen_sizeY, -100)
	if enemy.posX < screen_sizeX / 3:
		enemy.speedX = random.randint(0, 10) / 20 * enemy.speedY
	elif enemy.posX > screen_sizeX * 2 / 3:
		enemy.speedX = random.randint(-10, 0) / 20 * enemy.speedY
	else:
		enemy.speedX = random.randint(-5, 5) / 20 * enemy.speedY
	
def is_collision(object1, object2):

	obj1_midX = object1.posX + object1.sizeX
	obj1_midY = object1.posY + object1.sizeY
	obj2_midX = object2.posX + object2.sizeX
	obj2_midY = object2.posY + object2.sizeY

	# think if I want to improve this...
	distance = math.sqrt(math.pow(obj1_midX-obj2_midX,2) + math.pow(obj1_midY-obj2_midY,2))
	collision_limit = (object1.sizeX + object1.sizeY + object2.sizeX + object2.sizeY) / 5

	return distance < collision_limit

def show_explosion(object, image):
	screen.blit(image, (int(object.posX), int(object.posY)))


def show_online_score(font_size = 16, x=100, y=10):
	global score_list
	score_font = pygame.font.Font('freesansbold.ttf', font_size)

	sorted_user_scores = sorted(score_list, key=lambda x: x['score'], reverse=True)
	
	top_rank = []
	for user_score in sorted_user_scores:
		user_exists = next(filter(lambda x: x['user'] == user_score['user'], top_rank), None)
		if not user_exists:
			top_rank.append(user_score)

	y_pos = y
	for user_score in top_rank:
		name_text = score_font.render(f"{user_score['user']}: {user_score['score']}", True, (255, 255, 0))
		screen.blit(name_text, (screen_sizeX - x, y_pos))
		y_pos = y_pos + 5 + font_size


def show_score(score, level, name, coin_count, font_size = 16, x=10, y=10,stat_cluster="None", game_over=False, user_type=None):
	score_font = pygame.font.Font('freesansbold.ttf', font_size)
	level_text = score_font.render("Level  : " + str(level), True, (255, 255, 0))
	score_text = score_font.render("Score : " + str(score), True, (255, 255, 0))
	name_text = score_font.render("Name : " + str(name), True, (255, 255, 0))
	coin_text = score_font.render("Coin : " + str(coin_count), True, (255, 255, 0))
	
	if user_type:
		user_type_text = score_font.render("You are : " + str(user_type), True, (255, 255, 0))
	
	user_type_online_pred_text = score_font.render("Online Prediction: : " + str(stat_cluster), True, (255, 255, 0))

	y_pos = y
	screen.blit(level_text, (x, y_pos))
	y_pos = y_pos + 5 + font_size
	screen.blit(score_text, (x, y_pos))
	y_pos = y_pos + 5 + font_size
	screen.blit(name_text, (x, y_pos))
	y_pos = y_pos + 5 + font_size
	screen.blit(coin_text, (x, y_pos))
	y_pos = y_pos + 5 + font_size

	if user_type:
		y_pos = y_pos + 5 + font_size
		screen.blit(user_type_text, (x, y_pos))
	
	y_pos = y_pos + 5 + font_size
	screen.blit(user_type_online_pred_text, (x, y_pos))

	publish_online_score(score, name, game_over)


def publish_online_score(score, name, game_over):
	global publish_time, microgear
	sending_interval = 0.5
	now = datetime.now()
	if (now - publish_time).seconds >= sending_interval:
		data = dict(user=name, score=score)
		microgear.publish(user_score_topic, json.dumps(data))
		publish_time = now

 
def show_game_over(screen_sizeX, screen_sizeY, score, high_score, coin_count, user_type):
	
	# Move enemies below screen (is there a better way?)
	for i in range(num_of_enemies):
		enemy[i].posY = screen_sizeY + 100

	# Display text and score
	message_display_center('GAME OVER', font_large, yellow, int(screen_sizeX/2), int(screen_sizeY * 3/20))
	message_display_center('You\'re a', font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY * 3/10))
	message_display_center(user_type, font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY * 4/10))
	message_display_center('Score: ' + str(score), font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *5/10))
	message_display_center('Coins: ' + str(coin_count), font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *6/10))
	message_display_center('Highscore: ' + str(high_score), font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *7/10))
	message_display_center('Press any key to continue', font_medium, yellow, int(screen_sizeX/2), int(screen_sizeY *8/10))


#############################
#		Main Program		#
#############################
#if __name__ == '__main__':

# # initialize pygame 
# pygame.init()

# # Initialize fonts
# font_huge	= pygame.font.Font('freesansbold.ttf', 128)
# font_large	= pygame.font.Font('freesansbold.ttf', 64)
# font_medium	= pygame.font.Font('freesansbold.ttf', 32)
# font_small	= pygame.font.Font('freesansbold.ttf', 16)
# font_tiny	= pygame.font.Font('freesansbold.ttf', 8)


# Initialize Global CONSTANTS from space_wars_settings.py (sws)
MUSIC 		= False 		#sws.MUSIC 		# True
GAME_SPEED 	= 5 		#sws.GAME_SPEED 	# 1 to 5
PLAYER_NAME	= 'GZ'		#sws.PLAYER_NAME	# 'DAN'


# Initialize Global variables
screen_sizeX = 800
screen_sizeY = 600
screen_size = (screen_sizeX, screen_sizeY)
background_color = black
# Initialize screen
screen = pygame.display.set_mode((screen_sizeX, screen_sizeY))
# screen = pygame.display.set_mode((screen_sizeX, screen_sizeY), flags=pygame.FULLSCREEN)


# Get working directory and subdirectories
dir_path = os.getcwd()
images_path = os.path.join(dir_path, 'images')
sounds_path = os.path.join(dir_path, 'sounds')


# Initialize images
icon_image			= pygame.image.load(os.path.join(images_path , 'icon_07.png'))
player_image		= pygame.image.load(os.path.join(images_path, 'MilFal_03.png'))
bullet_image		= pygame.image.load(os.path.join(images_path, 'bullet.png'))
enemy_image	    	= [pygame.image.load(os.path.join(images_path, 'ufo_01.png')),
				       pygame.image.load(os.path.join(images_path, 'ufo_02.png')),
				       pygame.image.load(os.path.join(images_path, 'ufo_03.png')),
				       pygame.image.load(os.path.join(images_path, 'ufo_04.png')),
				       pygame.image.load(os.path.join(images_path, 'spaceship_03_usd.png')),
				       pygame.image.load(os.path.join(images_path, 'spaceship_01_usd.png')),
					   pygame.image.load(os.path.join(images_path, 'death_star_02.png')),
					   pygame.image.load(os.path.join(images_path, 'death_star_03.png'))]
coin_image			= pygame.image.load(os.path.join(images_path, 'coin.png'))
explosion_image		= [pygame.image.load(os.path.join(images_path, 'explosion_01.png')),
				       pygame.image.load(os.path.join(images_path, 'explosion_02.png'))]
background_image	= [pygame.image.load(os.path.join(images_path, 'background_03.jpg')), 
					   pygame.image.load(os.path.join(images_path, 'background_03_usd.jpg'))]
superweapon_image	= pygame.image.load(os.path.join(images_path, 'super_01.png'))

background_image_hight = 600
				      
# Caption and Icon
pygame.display.set_caption("Space Wars")
pygame.display.set_icon(icon_image)

# Initialize sounds
bullet_sound		= pygame.mixer.Sound(os.path.join(sounds_path, 'laser.wav'))
explosion_sound		= pygame.mixer.Sound(os.path.join(sounds_path, 'explosion.wav'))

# Start backgound music
if MUSIC:
	pygame.mixer.music.load(os.path.join(sounds_path, 'background.wav'))
	pygame.mixer.music.play(-1)

# Initialize game speed settings
frames_per_second = 20 + 10 * GAME_SPEED
clock = pygame.time.Clock()

# Initialize connection to high score database
db_connection = high_scores.high_scores_connect_to_db('high_scores.db')
high_scores.high_scores_create_table(db_connection)

# Initialize settings
player_maxSpeedX	= 3.5			# recommended: 3
player_maxSpeedY	= 3.5			# recommended: 3
enemy_maxSpeedX		= 2
enemy_maxSpeedY		= 2
bullet_speed		= 10

session_high_score 	= 0

# Initialize collection data
thread = None
A0 = [] # A0) Position in X axis => position X [1, 2, 3, 2, 1] / 5
A1 = [] # A1) Position in Y axis => position Y [200, 150, 130, 170] / 4
A2 = 0  # A2) Number of coins collected => Total
A3 = 0  # A3) Number of destroyed enemies => Total
A4 = 0  # A4) Number of shots => Total
A5 = 0  # A5) Number of shots without enemies => Total (A4 - A3)
A6 = 0  # A6) Level reach
A7 = 0  # A7) key X pressed count
A8 = 0  # A8) key Y pressed count
A9 = 0  # A9) Number of enemy created
A10 = 0  # A10) Number of coin created


def thread_collect_data():
    global thread, A0, A1, A2, A3, A4, A5, player
    if not go_to_menu and not quit_game:
	    A0 += [player.posX]
	    A1 += [player.posY]
	    thread = threading.Timer(1, thread_collect_data)
	    thread.start()

def save_collection_data(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count):
	global A0, A1
	A0 = statistics.mean(A0) if len(A0) else 0
	A1 = statistics.mean(A1) if len(A1) else 0
	A2 = coin_count
	A3 = destroyed_enemy_count
	A4 = shots_count
	A5 = A4 - A3
	A6 = level
	A7 = keyX_pressed_count
	A8 = keyY_pressed_count
	A9 = respawn_enemy_count
	A10 = respawn_coin_count
	if sum([A0, A1, A2, A3, A4, A5]) != 0:
		with open("train_data.txt", "a") as file_object:
			file_object.write(",".join(map(str, [A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, A10])))
			file_object.write("\n")

# --------------------
# Full Game Play Loop
# --------------------

quit_game = False
while not quit_game:

	# Start manu
	quit_game,glevel = menu()

	# Game settings
	num_of_enemies	= 5				# recommended: 5
	num_of_coins	= 5				# recommended: 5
	num_of_superw	= 5
	level_change	= 1000			# recommended: 1000
	level_score_increase = 10
	level_enemy_increase = 5

	# initialize other variables / counters
	score 		 = 0
	level		 = 1			# A6
	level_iter	 = 0
	loop_iter	 = 0
	keyX_pressed = 0
	keyY_pressed = 0
	game_over 	 = False
	go_to_menu 	 = False

	coin_count = 0				# A2
	destroyed_enemy_count = 0	# A3
	shots_count = 0				# A4
	keyX_pressed_count = 0		# A7
	keyY_pressed_count = 0		# A8
	respawn_enemy_count = 0		# A9
	respawn_coin_count = 0		# A10
	respawn_superw_count = 0

	g_enemy_count =0
	g_coin_count = 0
	g_shorts_count = 0
	straa="None"
	pre_score=0
	offline_pred = 0
	
	df_data = pd.DataFrame(columns=['coin_count', 'respawn_enemy_count', 'y_clustream','y_true','Ratio'])



	backgound_Y_lower = 0
	backgound_Y_upper = backgound_Y_lower - background_image_hight
	upper_index = 0
	lower_index = 1

	y_clustream_buff=0
	index=0
	coin_count_acc=0
	destroyed_enemy_count_acc=0


	# initialize player and bullet
	player = SpaceShip(player_image, explosion_image[0], screen_sizeX/2-32, screen_sizeY-100)
	bullet = Bullet(bullet_image, explosion_image[0], speedY = -bullet_speed, sound = bullet_sound, state = 'hide', sizeX = 32, sizeY = 32)
	
	model_posx = neighbors.KNNRegressor()
	model_posy = neighbors.KNNRegressor()

	scaler = preprocessing.StandardScaler()
	#model_posy = linear_model.LinearRegression()
	#metric = metrics.Accuracy()
	metric = metrics.MAE()

	clustream = cluster.CluStream(n_macro_clusters=2, max_micro_clusters=4, time_gap=3,seed=0, halflife=0.4) 
	metric_clustream = utils.Rolling(metrics.Accuracy(), window_size=3)
	'''
	model_classifier = ensemble.AdaBoostClassifier(
    model=(tree.HoeffdingTreeClassifier(
            split_criterion='gini',
            delta=1e-5,
            grace_period=2000
        )
    ),n_models=5,seed=42)
	'''
	model_classifier = forest.ARFClassifier(seed=8, leaf_prediction="mc")

	posx = 0
	posy = 0
	old_posx = 0
	old_posy = 0

	predic_posx = 0
	predic_posy = 0

	first_touch = 0

	if glevel >1:
		model_posx.learn_one({'x':float(old_posx)}, float(posx))
		model_posy.learn_one({'y':float(old_posy)}, float(posy))

	# initialize enemies
	enemy = []
	enemy_image_index = 0
	for i in range(num_of_enemies):
		enemy.append(SpaceEnemy(enemy_image[enemy_image_index], explosion_image[1], speedY = level, hit_points = level))
		respawn(enemy[i], level)
		respawn_enemy_count += 1

	# initialize coins
	coins = []
	for i in range(num_of_coins):
		coins.append(SpaceCoin(coin_image, explosion_image[0], speedY = level, hit_points = 1))
		respawn(coins[i], level)
		respawn_coin_count += 1
	
	# initialize super respawn_superw_count
	superw = []
	if glevel >1:
		for i in range(num_of_superw):
			superw.append(SuperWeapon(superweapon_image, explosion_image[0], speedY = level+4, hit_points = 1))
			respawn2(superw[i],predic_posx, level, glevel)

			respawn_superw_count += 1

	# initialize collection data
	thread = None
	A0 = []
	A1 = []
	A2 = 0
	A3 = 0
	A4 = 0
	A5 = 0
	A6 = 0
	A7 = 0
	A8 = 0
	A9 = 0
	A10 = 0
	thread_collect_data()

	actual_posX = []
	actual_posY = []
	predicted_posX = []
	predicted_posY = []
	timestamp = []
	list_enemy_count = []
	list_coin_count = []
	list_shots_count = []
	list_cluster = []
	list_class =[]
	list_score = []
	list_offline = []
	'''
	list_A0 = []
	list_A1 = []
	list_A2 = []
	list_A3 = []
	list_A4 = []
	list_A5 = []
	list_A6 = []
	list_A7 = []
	list_A8 = []
	list_A9 = []
	list_A10 = []
	'''
	# --------------------
	# Main Game Play Loop
	# --------------------
	previous_timestamp = datetime.now()
	while not go_to_menu and not quit_game:

		current_timestamp = datetime.now()

		# Fill screen and background image	
		screen.fill(background_color)

		# Background images moving
		backgound_Y_lower += 1
		backgound_Y_upper += 1
		if backgound_Y_lower > screen_sizeY:
			backgound_Y_lower = backgound_Y_upper
			backgound_Y_upper = backgound_Y_lower - background_image_hight
			temp = upper_index
			upper_index = lower_index
			lower_index = temp
		screen.blit(background_image[upper_index], (0,backgound_Y_upper))
		screen.blit(background_image[lower_index], (0,backgound_Y_lower))

		# check if increase level
		level_iter += 1
		if level_iter > level_change and not game_over:
			level_iter = 0
			level += 1

			# increase number of enemies with higher speed
			enemy_image_index = (level -1) % len(enemy_image)
			for i in range(num_of_enemies, num_of_enemies+level_enemy_increase):
				enemy.append(SpaceEnemy(enemy_image[enemy_image_index], explosion_image[1], speedY = level, hit_points = level))
				respawn(enemy[i], level)
				respawn_enemy_count += 1
			num_of_enemies	+= level_enemy_increase

			# increase number of coin with same speed
			for i in range(num_of_coins, num_of_coins + num_of_coins):
				coins.append(SpaceCoin(coin_image, explosion_image[0], speedY = level, hit_points = 1))
				respawn(coins[i], level)
				respawn_coin_count += 1

			# increase number of coin with same speed
			if glevel >1:
				for i in range(num_of_superw, num_of_superw + num_of_superw):
					superw.append(SuperWeapon(superweapon_image, explosion_image[0], speedY = level, hit_points = 1))
					respawn2(superw[i],predic_posx, level,glevel)

					respawn_superw_count += 1

			# increase score when reaching new level
#			score += level_score_increase

		# Check events and take action
		for event in pygame.event.get():	
			if event.type == pygame.QUIT:
				quit_game = True	

			# if key is pressed
			if event.type == pygame.KEYDOWN:
				
				first_touch = 1
				# if Game Over and any key, go to menu 				
				if game_over:
					go_to_menu = True

				

				# 'p' or ESC' for pause 
				elif event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
				 	paused(screen_sizeX, screen_sizeY)

				# 'arrow keys' for movement
				elif event.key == pygame.K_LEFT:
					player.speedX = -player_maxSpeedX
					keyX_pressed += 1
					keyX_pressed_count += 1
				elif event.key == pygame.K_RIGHT:
					player.speedX = player_maxSpeedX
					keyX_pressed += 1
					keyX_pressed_count += 1
				elif event.key == pygame.K_UP:
					player.speedY = -player_maxSpeedY
					keyY_pressed += 1
					keyY_pressed_count += 1
				elif event.key == pygame.K_DOWN:
					player.speedY = player_maxSpeedY
					keyY_pressed += 1
					keyY_pressed_count += 1

				# if space key, fire bullet			
				elif (event.key == pygame.K_SPACE or event.key == pygame.K_a) and bullet.state == 'hide':
					bullet.fire_bullet(player)
					shots_count += 1
					

			# if key is released, stop movement in a nice way
			if event.type == pygame.KEYUP:
				first_touch = 1
				if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
					keyX_pressed -= 1
					if keyX_pressed == 0:
						player.speedX = 0
				if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
					keyY_pressed -= 1
					if keyY_pressed == 0:
						player.speedY = 0



		# Move player and check not out of screen
		#print()
		if (game_over != True) and (first_touch >0):
			predic_posx = model_posx.predict_one({'x':float(old_posx)})
			predic_posy = model_posy.predict_one({'y':float(old_posy)})

			posx,posy = player.update_player_postion(screen_sizeX, screen_sizeY)

			# Add to the respective lists:
			actual_posX.append(posx)
			actual_posY.append(posy)
			predicted_posX.append(predic_posx)
			predicted_posY.append(predic_posy)
			current_time = datetime.now()
			formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")
			timestamp.append(formatted_time)
			#ddata = {'coin_count': (coin_count - g_coin_count), 'destory_enemy_count':(destroyed_enemy_count - g_enemy_count)}
			#ddata = {0: (coin_count - g_coin_count), 1:(destroyed_enemy_count - g_enemy_count)}
			coin_count_acc += coin_count
			destroyed_enemy_count_acc += destroyed_enemy_count
			ddata = {0: (coin_count_acc), 1:(destroyed_enemy_count_acc)}
			
			buff_data =ddata
			list_enemy_count.append(destroyed_enemy_count - g_enemy_count)
			g_enemy_count = destroyed_enemy_count

			list_coin_count.append(coin_count - g_coin_count)
			g_coin_count = coin_count
			list_shots_count.append(shots_count - g_shorts_count)
			g_shorts_count = shots_count
			#print(f": {ddata}")
			ddata = scaler.learn_one(ddata).transform_one(ddata)
			#print(f"==> {ddata}")
			clustream = clustream.learn_one(ddata)
			y_clustream = clustream.predict_one(ddata)

			'''
			df_unit = pd.DataFrame({
				'coin_count': coin_count,
				'respawn_enemy_count': destroyed_enemy_count,
				'y_clustream': y_clustream
    		})
			'''

			Row={'coin_count': coin_count, 'respawn_enemy_count': destroyed_enemy_count, 'y_clustream': y_clustream}
			#print(f"Row= {Row}")
			df_data = df_data._append(Row, ignore_index=True)



			buff_coin_count = df_data['coin_count'].iloc[index]
			buff_respawn_enemy_count = df_data['respawn_enemy_count'].iloc[index]

			if buff_coin_count <=0:
				buff_coin_count = 10**(-4)

			if buff_respawn_enemy_count <= 0:
				buff_respawn_enemy_count = 10**(-4)
			
			ratio = (buff_coin_count - buff_respawn_enemy_count) / (buff_coin_count + buff_respawn_enemy_count)
			df_data['Ratio'].iloc[index] = ratio
			latest_ratio = ratio
			#print(f"==> {ratio} , {df_data.iloc[:index + 1].groupby('y_clustream')['Ratio']} ")
			mean_ratios = df_data.iloc[:index + 1].groupby('y_clustream')['Ratio'].mean()
			latest_y_clustream = df_data['y_clustream'].iloc[index]
			coin_kill_ratio = buff_coin_count / buff_respawn_enemy_count
			
			#print(f"mean_ratios = {mean_ratios}")
			if len(mean_ratios) == 2:
				if df_data['Ratio'].iloc[index] >= 0:  # coin_count > respawn_enemy_count
					if (mean_ratios[0] > 0) and (mean_ratios[1] > 0):
						if latest_y_clustream == 0:
							if mean_ratios[latest_y_clustream] < mean_ratios[1]:
								df_data['y_true'].iloc[index] = 1  # Casual Achiever
							else:
								df_data['y_true'].iloc[index] = 2  # Hardcore Achiever
						elif latest_y_clustream == 1:
							if mean_ratios[latest_y_clustream] < mean_ratios[0]:
								df_data['y_true'].iloc[index] = 1  # Casual Achiever
							else:
								df_data['y_true'].iloc[index] = 2  # Hardcore Achiever
					elif (mean_ratios[0] < 0) and (mean_ratios[1] < 0):
						if latest_y_clustream == 0:
							if mean_ratios[latest_y_clustream] > mean_ratios[1]:
								df_data['y_true'].iloc[index] = 1  # Casual Achiever
							else:
								df_data['y_true'].iloc[index] = 2  # Hardcore Achiever
						elif latest_y_clustream == 1:
							if mean_ratios[latest_y_clustream] > mean_ratios[0]:
								df_data['y_true'].iloc[index] = 1  # Casual Achiever
							else:
								df_data['y_true'].iloc[index] = 2  # Hardcore Achiever
					elif (mean_ratios[0] < 0) and (mean_ratios[1] > 0):
						if latest_y_clustream == 0:
							if mean_ratios[latest_y_clustream] < mean_ratios[1]:
								df_data['y_true'].iloc[index] = 1  # Casual Achiever
							else:
								df_data['y_true'].iloc[index] = 2  # Hardcore Achiever
						elif latest_y_clustream == 1:
							if mean_ratios[latest_y_clustream] > mean_ratios[0]:
								df_data['y_true'].iloc[index] = 1  # Casual Achiever
							else:
								df_data['y_true'].iloc[index] = 2  # Hardcore Achiever
					elif (mean_ratios[0] > 0) and (mean_ratios[1] < 0):
						if latest_y_clustream == 0:
							if mean_ratios[latest_y_clustream] > mean_ratios[1]:
								df_data['y_true'].iloc[index] = 1  # Casual Achiever
							else:
								df_data['y_true'].iloc[index] = 2  # Hardcore Achiever
						elif latest_y_clustream == 1:
							if mean_ratios[latest_y_clustream] < mean_ratios[0]:
								df_data['y_true'].iloc[index] = 1  # Casual Achiever
							else:
								df_data['y_true'].iloc[index] = 2  # Hardcore Achiever
				elif df_data['Ratio'].iloc[index] < 0:  # coin_count < respawn_enemy_count
					if (mean_ratios[0] > 0) and (mean_ratios[1] > 0):
						if latest_y_clustream == 0:
							if mean_ratios[latest_y_clustream] < mean_ratios[1]:
								df_data['y_true'].iloc[index] = 3  # Hardcore Killer
							else:
								df_data['y_true'].iloc[index] = 4  # Casual Killer
						elif latest_y_clustream == 1:
							if mean_ratios[latest_y_clustream] < mean_ratios[0]:
								df_data['y_true'].iloc[index] = 3  # Hardcore Killer
							else:
								df_data['y_true'].iloc[index] = 4  # Casual Killer
					elif (mean_ratios[0] < 0) and (mean_ratios[1] < 0):
						if latest_y_clustream == 0:
							if mean_ratios[latest_y_clustream] > mean_ratios[1]:
								df_data['y_true'].iloc[index] = 4  # Hardcore Killer
							else:
								df_data['y_true'].iloc[index] = 3  # Casual Killer
						elif latest_y_clustream == 1:
							if mean_ratios[latest_y_clustream] > mean_ratios[0]:
								df_data['y_true'].iloc[index] = 4  # Hardcore Killer
							else:
								df_data['y_true'].iloc[index] = 3  # Casual Killer
					elif (mean_ratios[0] < 0) and (mean_ratios[1] > 0):
						if latest_y_clustream == 0:
							if mean_ratios[latest_y_clustream] < mean_ratios[1]:
								df_data['y_true'].iloc[index] = 4  # Hardcore Killer
							else:
								df_data['y_true'].iloc[index] = 3  # Casual Killer
						elif latest_y_clustream == 1:
							if mean_ratios[latest_y_clustream] > mean_ratios[0]:
								df_data['y_true'].iloc[index] = 4  # Hardcore Killer
							else:
								df_data['y_true'].iloc[index] = 3  # Casual Killer
					elif (mean_ratios[0] > 0) and (mean_ratios[1] < 0):
						if latest_y_clustream == 0:
							if mean_ratios[latest_y_clustream] > mean_ratios[1]:
								df_data['y_true'].iloc[index] = 4  # Hardcore Killer
							else:
								df_data['y_true'].iloc[index] = 3  # Casual Killer
						elif latest_y_clustream == 1:
							if mean_ratios[latest_y_clustream] < mean_ratios[0]:
								df_data['y_true'].iloc[index] = 4  # Hardcore Killer
							else:
								df_data['y_true'].iloc[index] = 3  # Casual Killer
			
			elif len(mean_ratios) == 1:
				if df_data['Ratio'].iloc[index] >= 0: # coin_count > respawn_enemy_count
					if (coin_kill_ratio >= 1) & (coin_kill_ratio < 1.5):
						df_data['y_true'].iloc[index] = 1 # Casual Achiever
					elif coin_kill_ratio >= 1.5:
						df_data['y_true'].iloc[index] = 2 # Hardcore Achiever
				elif df_data['Ratio'].iloc[index] <= 0:
					if (coin_kill_ratio < 1) & (coin_kill_ratio > 0.5):
						df_data['y_true'].iloc[index] = 3 # Casual Killer
					elif coin_kill_ratio <= 0.5:
						df_data['y_true'].iloc[index] = 4 # Hardcore Killer
			


			#print(df_data['y_true'].value_counts())
			
			y_clustream_buff = df_data['y_true'].value_counts().reset_index()
			y_cluster_pred = y_clustream_buff.loc[0,['y_true']]['y_true']
			
			y_classifi_pred = model_classifier.predict_one(buff_data)
			#model_classifier = model_classifier.learn_one(buff_data, int(y_cluster_pred['y_true']))
			model_classifier = model_classifier.learn_one(buff_data, int(y_cluster_pred))

			list_cluster.append(y_cluster_pred)
			list_class.append(y_classifi_pred)
			list_score.append(score)
			pre_score = score
			offline_pred = prediction_user_type_ex(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count) +1
			list_offline.append(offline_pred)

			index += 1

			'''
			if y_clustream_buff != y_clustream:
				#	print(f"{ddata} => {y_clustream}")
				#print("------------------------------------------")
				y_clustream_buff = y_clustream
				print(f"{ddata} => {y_clustream} => {buff_data}")
			'''
			if (current_timestamp - previous_timestamp).total_seconds() >= 5:
				#print_message()
				#print("#####")
				cctime = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")
				print(f'## {cctime} ##')
				print('index:', index)
				print('latest_y_clustream:', latest_y_clustream)
				print('latest_ratio:',latest_ratio)
				if len(mean_ratios) < 1:
					print(f'mean_ratio: not available')
				else:
					print(f'mean_ratio:{mean_ratios[0]} , {mean_ratios[1]}\n')

				try:
					aa = df_data['y_true'].value_counts().reset_index()
					print(aa)
					print(f"Cluster ={aa.loc[0,['y_true']]}, Class ={y_classifi_pred}")
					#print(f"Rank = {aa.loc[0,['y_true','count']]}")
					straa= LABELS_ONLINE.get(int(aa.loc[0,['y_true']]) - 1)
				except KeyError:
					print("unknow data [y_true]")
				previous_timestamp = current_timestamp
			


		bullet.update_bullet_position(screen_sizeX, screen_sizeY)

		#distance = math.sqrt(((predic_posx - posx)**2) + ((predic_posy - posy)**2)) math.pow(
		distance = math.sqrt(math.pow(predic_posx - posx,2) + math.pow(predic_posy - posy,2))
		if (distance > 10):
			#print(f"old={old_posx} posx={posx} , predic_posx={float(predic_posx)} , {predic_posx} {distance}")
			#print(f"old={old_posy} posy={posy} , predic_posy={float(predic_posy)} , {predic_posy}")

			model_posx.learn_one({'x':float(old_posx)}, float(posx))
			metric.update(float(old_posx), float(posx))
			model_posy.learn_one({'y':float(old_posy)}, float(posy))
			metric.update(float(old_posy), float(posy))

		old_posx = posx
		old_posy = posy

		


		if game_over:
			player.explosion_counter = 0
			thread.cancel()
			user_type = prediction_user_type(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count)
			show_game_over(screen_sizeX, screen_sizeY, score, session_high_score, coin_count, user_type)
			show_score(score, level, PLAYER_NAME, coin_count,stat_cluster=str(straa), game_over=True)
			show_online_score()
			
			df = pd.DataFrame({
				'timestamp': timestamp,
        		'pos_x': actual_posX,
        		'predicted_pos_x': predicted_posX,
        		'pos_y': actual_posY,
        		'predicted_pos_y': predicted_posY,
				'coin_count': list_coin_count,
				'shots_count': list_shots_count,
				'destory_enemy_count': list_enemy_count,
				'score':list_score,
				'y_pred_cluster': list_cluster,
				'y_pred_class': list_class,
				'y_pred_offline':list_offline
    		})
			df.to_csv('positions.csv', index=False)


		else:
			
			# Move enemies and check collisions
			for i in range(num_of_enemies):
				
				# if enemy exploding
				if enemy[i].explosion_counter >= 1:
					enemy[i].explosion_counter -= 1
				elif enemy[i].explosion_counter == 0:
					respawn(enemy[i], level)
					#print("Add enemy")
					respawn_enemy_count += 1
				else:
					enemy[i].update_enemy_position(screen_sizeX, screen_sizeY)
					if enemy[i].posY > screen_sizeY:
						respawn(enemy[i], level)
						# respawn_enemy_count += 1
					enemy[i].show()
					
					# if enemy collision with player
					if is_collision(enemy[i], player):
						explosion_sound.play()
						player.explosion_counter = 5
						if score > session_high_score:
							session_high_score = score
						game_over = True
					
					# if bullet hits enemy 
					elif bullet.state == 'show' and is_collision(enemy[i], bullet) :
						explosion_sound.play()
						enemy[i].explosion_counter = 10
						score += enemy[i].hit_points
						destroyed_enemy_count += 1
						bullet.state = 'hide'

				enemy[i].show()

			# Move coins and check collisions
			for i in range(num_of_coins):
				
				# if coin exploding
				if coins[i].explosion_counter >= 1:
					coins[i].explosion_counter -= 1
				elif coins[i].explosion_counter == 0:
					respawn(coins[i], level)		
					respawn_coin_count += 1
				else:
					coins[i].update_coin_position(screen_sizeX, screen_sizeY)
					if coins[i].posY > screen_sizeY:
						respawn(coins[i], level)
						# respawn_coin_count += 1
					coins[i].show()

					# if coin collision with player
					if is_collision(coins[i], player):
						coins[i].explosion_counter = 0
						score += coins[i].hit_points
						coin_count += 1

				coins[i].show()

			# Move superw and check collisions
			if glevel >1:

				for i in range(num_of_coins):
				
					# if coin exploding
					if superw[i].explosion_counter >= 1:
						superw[i].explosion_counter -= 1
					elif superw[i].explosion_counter == 0:
						respawn2(superw[i],predic_posx, level,glevel)		
						respawn_superw_count += 1
					else:
						superw[i].update_superweapon_position(screen_sizeX, screen_sizeY)
						if superw[i].posY > screen_sizeY:
							respawn2(superw[i],predic_posx, level,glevel)
							# respawn_coin_count += 1
						superw[i].show()

						# if coin collision with player
						'''
						if is_collision(superw[i], player):
							superw[i].explosion_counter = 0
							score += superw[i].hit_points
							coin_count += 1
						'''
						# if enemy collision with player
					
						if is_collision(superw[i], player):
							explosion_sound.play()
							player.explosion_counter = 5
							if score > session_high_score:
								session_high_score = score
							game_over = True
					

					superw[i].show()

			# show player
			bullet.show()
			player.show()
			user_type = prediction_user_type(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count)
			show_score(score, level, PLAYER_NAME, coin_count,stat_cluster=str(straa), user_type=user_type)
			show_online_score()

		pygame.display.flip()
		
		clock.tick(frames_per_second)

		if player.explosion_counter > 0 :
			# to freeze and show player explosion longer
			time.sleep(1)

	# Update High Score database
	if score > 0:
		high_scores.high_scores_update_db(db_connection, PLAYER_NAME, score)

	save_collection_data(level, keyX_pressed_count, keyY_pressed_count, respawn_enemy_count, respawn_coin_count)

db_connection.close()
print('Successfully quit Space Wars!')
