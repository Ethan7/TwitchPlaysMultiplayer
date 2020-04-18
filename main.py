# By Ethan #
# Written on 4/8/2020 #

#Define the imports
import twitch
import cocos
from cocos.director import director
import pyglet
from pyglet.window import mouse
import pymunk
#from pymunk import Vec2d
#from pymunk.pyglet_util import DrawOptions
import threading
import math
import random

#check if mouse is overlapping sprite
def mouse_on_sprite(sprite, x, y, player):
	if x > sprite.x-sprite.width/2 and x < sprite.x+sprite.width/2 and y > sprite.y - sprite.height/2 and y < sprite.y + sprite.height/2 and player:
		return True;
	elif x > sprite.x and x < sprite.x+sprite.width and y > sprite.y and y < sprite.y + sprite.height and not player:
		return True;
	else:
		return False;

#reset the game and delete all obstacles
def reset(arbiter, space, data):
	winlabel.element.text=data[arbiter.shapes[0]]+" has reached the objective";
	objective.position = (window.width-objective.width, window.height-objective.height);
	objective.body.position = objective.position;
	for player in players.values():
		player.body.position = (random.random(window.width-64), random.random(window.height-64));
		player.body._set_velocity((0,0));
	for obstacle in obstacles:
		space.remove(obstacle.shape);
		obstacle.kill();
		obstacles.remove(obstacle);
	return False;

#player sprite, physics body, and label
class playerSprite(cocos.sprite.Sprite):
	def __init__(self, name):
		super().__init__("img/playerSprite.png");
		self.name = name;
		self.label = cocos.text.Label(name, font_name="Arial", font_size=16, color=(255,255,255, 255), anchor_x="center");
		self.label.position = 0, 0;
		self.position = 0, 0;

		self.shape = pymunk.Poly.create_box(None, size=(self.width, self.height));
		self.moment = pymunk.moment_for_poly(1, self.shape.get_vertices());
		self.body = pymunk.Body(1, self.moment); #Mass and Moment of Inertia
		self.shape.body = self.body;
		self.shape.elastivity = 0.3;
		self.shape.friction = 0.2;
		self.shape._set_collision_type(1);

		self.mousemove = False;
		self.storedvx = 0;
		self.storedvy = 0;

#background image and keyboard/mouse handler
class newLayer(cocos.layer.Layer):
	is_event_handler = True;
	def __init__(self):
		super().__init__();
		self.spr = cocos.sprite.Sprite("img/backdrop.png");
		self.spr.position = (0, 0);
		self.add(self.spr);
	def on_mouse_press(self, x, y, buttons, modifiers):
		for player in players.values():
			if buttons == pyglet.window.mouse.LEFT and mouse_on_sprite(player, x, y, 1):
				player.mousemove = True;
		if buttons == pyglet.window.mouse.LEFT and mouse_on_sprite(objective, x, y, 1):
			objective.mousemove = True;
		for obstacle in obstacles:
			if buttons == pyglet.window.mouse.MIDDLE and mouse_on_sprite(obstacle, x, y, 0):
				space.remove(obstacle.shape);
				obstacle.kill();
				obstacles.remove(obstacle);
		if buttons == pyglet.window.mouse.RIGHT:
			self.newLeft = x;
			self.newBottom = y;
	def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
		for player in players.values():
			if player.mousemove:
				player.body.position = (x, y);
				player.body.sleep();
				player.storedvx = dx;
				player.storedvy = dy;
		if objective.mousemove:
			objective.position = (x, y);
			objective.body.position = (x, y);
			objective.storedvx = dx;
			objective.storedvy = dy;
	def on_mouse_release(self, x, y, buttons, modifiers):
		if buttons == pyglet.window.mouse.LEFT:
			for player in players.values():
				if player.mousemove:
					player.mousemove = False;
					player.body.activate();
					player.body._set_velocity((player.storedvx*10, player.storedvy*10));
			if objective.mousemove:
				objective.mousemove = False;
		if buttons == pyglet.window.mouse.RIGHT:
			obstacle = cocos.layer.util_layers.ColorLayer(0, 255, 0, 255, width=abs(x-self.newLeft), height=abs(y-self.newBottom));
			obstacle.position = (self.newLeft, self.newBottom);
			game_scene.add(obstacle);
			obstacle.shape = pymunk.Poly.create_box(space.static_body, size=(obstacle.width, obstacle.height));
			obstacle.shape.elastivity = 0.8;
			obstacle.shape.friction = 1.0;
			obstacle.shape.body.position = (obstacle.x+obstacle.width/2, obstacle.y+obstacle.height/2);
			space.add(obstacle.shape);
			obstacles.append(obstacle);
	def on_key_press(self, symbol, modifiers):
		if symbol == 32:
			for player in players.values():
				player.body.position = (random.random(window.width-64), random.random(window.height-64));
				player.body._set_velocity((0,0));

#add new player from twitch chat
def create_user(user):
	players[user] = playerSprite(user);
	game_scene.add(players[user]);
	game_scene.add(players[user].label);
	players[user].body.position = (random.random(window.width-64), random.random(window.height-64));
	space.add(players[user].shape, players[user].body);
	handler.data[players[user].shape] = user; #store the name of the player inside the collision handler data

#take input from player from twitch chat
def game_input(user, input):
	if(input == "jump"):
		#players[user].body.apply_impulse_at_local_point(Vec2d.unit()*1000, (0, 16));
		players[user].body._set_velocity((0, 500));
	elif(input == "left"):
		#players[user].body.apply_impulse_at_local_point(Vec2d.unit()*500, (players[user].width, 0));
		players[user].body._set_velocity((-200, 0));
	elif(input == "right"):
		#players[user].body.apply_impulse_at_local_point(Vec2d.unit()*500, (-1*players[user].width, 0));
		players[user].body._set_velocity((200, 0));
	elif(input == "jumpleft"):
		players[user].body._set_velocity((-200, 500));
	elif(input == "jumpright"):
		players[user].body._set_velocity((200, 500));
	elif(input == "random"):
		players[user].body._set_velocity((random.randrange(-1000, 1000), random.random(1000)));

#handle twitch networking in separate thread to speed up performance
def twitch_thread():
	global new_messages;
	new_messages = t.twitch_recieve_messages();

#the main loop
def update(dt):
	global time;
	global t1;
	#Check for new mesasages
	if time > timeout:
		t1.join();
		if new_messages:
			for message in new_messages:
				#Wuhu we got a message. Let's extract some details from it
				msg = message['message'].lower()
				username = message['username'].lower()
				print(username + ": " + msg);
				if(username not in users):
					users.append(username);
					create_user(username);
	
				#This is where you change the keys that shall be pressed and listened to.
				#The code below will simulate the key q if "q" is typed into twitch by someone
				#.. the same thing with "w"
				#Change this to make Twitch fit to your game!
				if msg[:6] == "input:": game_input(username, msg[6:]);
		time = 0;
	if(time == 0.0):
		t1 = threading.Thread(target=twitch_thread);
		t1.start();
	time += dt;
	space.step(dt);
	for player in players.values():
		player.position = player.body.position;
		player.rotation = (player.body.angle*180.0)/math.pi; #convert radians to degrees
		player.label.position = (player.x, player.y+player.height);
		if not bound_box.contains_vect(player.body.position):
			player.body.position = (random.random(window.width-64), random.random(window.height-64));
			player.body._set_velocity((0,0));

#globals
players = {};
obstacles = [];
time = 0.0;

#twitch code
t = twitch.Twitch();
users = [];
new_messages = [];
 
#Enter your twitch username and oauth-key below, and the app connects to twitch with the details.
#Your oauth-key can be generated at http://twitchapps.com/tmi/
username = "insert_username_here";
key = "insert_oauth_key_here";
t.twitch_connect(username, key);
timeout = t.s.gettimeout()+0.1;

#threads code
t1 = threading.Thread(target=twitch_thread);

#cocos2d Code
window = director.init(width=1280, height=720, caption="Ethan's Game Stream");
#options = DrawOptions();

mouse_layer = newLayer();
game_scene = cocos.scene.Scene(mouse_layer);

winlabel = cocos.text.Label("", font_name="Arial", font_size=16, color=(255,255,255, 255), anchor_x="center");
winlabel.position = window.width/2, window.height/2;
game_scene.add(winlabel);

pyglet.clock.schedule_interval(update, 1.0/60);

#Pymunk Code
space = pymunk.Space();
space._set_sleep_time_threshold(5);
space.gravity = 0, -1000;
bound_box = pymunk.BB(0, 0, window.width, window.height);
handler = space.add_collision_handler(1, 2);
handler._set_pre_solve(reset);

#objective
objective = cocos.sprite.Sprite("img/objective.png");
objective.position = (window.width-objective.width, window.height-objective.height);
objective.shape = pymunk.Poly.create_box(None, size=(objective.width, objective.height));
objective.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC); #Mass and Moment of Inertia
objective.shape.body = objective.body;
objective.shape.elastivity = 0.0;
objective.shape.friction = 0.0;
objective.shape._set_collision_type(2);
objective.body.position = objective.position;
objective.storedvx = 0;
objective.storedvy = 0;
objective.mousemove = False;
game_scene.add(objective);
space.add(objective.shape, objective.body);

#boundary sides
segment_shape1 = pymunk.Segment(space.static_body, (0,0), (window.width,0), 5);
segment_shape1.elasticity = 0.0;
segment_shape1.friction = 1.0;
segment_shape1.body.position = 0, 0;
space.add(segment_shape1);

segment_shape2 = pymunk.Segment(space.static_body, (0,0), (window.width,0), 5);
segment_shape2.elasticity = 0.0;
segment_shape2.friction = 1.0;
segment_shape2.body.position = 0, window.height;
space.add(segment_shape2);

segment_shape3 = pymunk.Segment(space.static_body, (0,0), (0,window.height), 5);
segment_shape3.elasticity = 0.0;
segment_shape3.friction = 1.0;
segment_shape3.body.position = 0, 0;
space.add(segment_shape3);

segment_shape4 = pymunk.Segment(space.static_body, (0,0), (0,window.height), 5);
segment_shape4.elasticity = 0.0;
segment_shape4.friction = 1.0;
segment_shape4.body.position = window.width, 0;
space.add(segment_shape4);

#@window.event
#def on_draw():
#	space.debug_draw(options);

#create_user("test");

director.run(game_scene);