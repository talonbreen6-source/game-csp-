# ...existing code...
import turtle
import time
import random
import os
import math
x=turtle
# --- Setup Screen ---
wn = turtle.Screen()
wn.title("Geometry Dash")
wn.bgcolor("black")
wn.setup(width=800, height=400)


x.penup()
x.goto(-450,-112)
x.pendown()
x.fillcolor("white")
x.begin_fill()
x.speed(5000)
x.forward(1000)
x.right(90)
x.forward(1000)
x.right(90)
x.forward(1000)
x.right(90)
x.forward(1000)
x.end_fill()


wn.tracer(0) # Turns off automatic screen updates for smoother animation


# --- Player (Cube) ---
player = turtle.Turtle()
player.shape("square")
player.color("blue")
player.penup()
player.goto(-300, -100)
player.dy = 0 # Vertical velocity
player.ducking = False
player.duck_timer = 0
player.shapesize(1,1)


# --- Obstacles
def create_ground_spike(x=400):
    s = turtle.Turtle()
    s.shape("triangle")
    s.color("red")
    s.penup()
    s.type = "ground"
    s.w = 20
    s.h = 30
    s.goto(x, -105)
    s.setheading(90) # Point up
    s.scored = False
    return s


def create_ceiling_block(x=400):
    s = turtle.Turtle()
    s.shape("square")
    s.shapesize(1,5) # tall and narrow
    s.color("gray")
    s.penup()
    s.type = "ceiling"
    s.w = 60
    s.h = 40
    s.goto(x, -76)  # positioned overhead; player must duck
    s.scored = False
    return s


def create_moving_obstacle(x=400):
    s = turtle.Turtle()
    s.shape("square")
    s.color("orange")
    s.penup()
    s.type = "moving"
    s.w = 30
    s.h = 30
    s.base_y = -60
    s.amp = random.randint(20, 60)
    s.phase = random.random() * 2 * math.pi
    s.speed_phase = random.uniform(0.05, 0.12)
    s.goto(x, s.base_y)
    s.scored = False
    return s


def create_double_spikes(x=400):
    # two ground spikes close together (requires longer jump)
    s1 = create_ground_spike(x)
    s2 = create_ground_spike(x + 30)
    return [s1, s2]


spikes = []
spikes.append(create_ground_spike(300))  # initial spike


# --- Scoreboard ---
score = 0
high_score = 0
hs_path = "highscore.txt"
if os.path.exists(hs_path):
    try:
        with open(hs_path, "r") as f:
            high_score = int(f.read().strip() or 0)
    except:
        high_score = 0


scoreboard = turtle.Turtle()
scoreboard.hideturtle()
scoreboard.penup()
scoreboard.color("white")
scoreboard.goto(-380, 160)


controls = turtle.Turtle()
controls.hideturtle()
controls.penup()
controls.color("white")
controls.goto(120,160)
controls.write("Space=Jump  Down/S=Duck", False, align="left", font=("Arial",14, "normal"))


def update_scoreboard():
    scoreboard.clear()
    scoreboard.write(f"Score: {score}   High: {high_score}", False, align="left", font=("Arial", 15, "normal"))


update_scoreboard()


# --- Physics & Controls ---
gravity = -.5


def jump():
    if player.ycor() <= -100 and not player.ducking: # Only jump if on the ground and not ducking
        player.dy = 10


def duck():
    if player.ycor() <= -100 and not player.ducking:
        player.ducking = True
        player.duck_timer = 50  # frames to stay ducked
        player.shapesize(0.5,1) # shorter to go under ceilings


wn.listen()
wn.onkeypress(jump, "space")
wn.onkeypress(duck, "Down")
wn.onkeypress(duck, "s")


# --- Spawn & Difficulty ---
spawn_timer = 0
spawn_interval =115  # ticks between spawns
min_interval = 30
spawn_speedup_timer = 0
speed = 7.5


# --- Main Game Loop ---
while True:
    wn.update() # Manually update the screen


    # Player Gravity and duck timer
    if player.ducking:
        player.duck_timer -= 1
        if player.duck_timer <= 0:
            player.ducking = False
            player.shapesize(1,1)
    player.dy += gravity
    player.sety(player.ycor() + player.dy)


    # Ground detection
    if player.ycor() <= -100:
        player.sety(-100)
        player.dy = 0


    # Spawn new obstacles over time with variety
    spawn_timer += 1
    spawn_speedup_timer += 1
    if spawn_timer >= spawn_interval:
        spawn_timer = 0
        r = random.random()
        new_x = 400 + random.randint(0, 100)
        if r < 0.55:
            spikes.append(create_ground_spike(new_x))
        elif r < 0.7:
            spikes.extend(create_double_spikes(new_x))
        elif r < 0.9:
            spikes.append(create_ceiling_block(new_x))
        else:
            spikes.append(create_moving_obstacle(new_x))


    # Gradually increase difficulty by reducing spawn interval
    if spawn_speedup_timer >= 600 and spawn_interval > min_interval:
        spawn_speedup_timer = 0
        spawn_interval = max(min_interval, spawn_interval - 15)


    # Move obstacles, update moving ones, score when passed, and remove off-screen ones
    for s in spikes[:]:
        # moving obstacle oscillation
        if getattr(s, "type", "") == "moving":
            s.phase += s.speed_phase
            y = s.base_y + math.sin(s.phase) * s.amp
            s.sety(y)
        s.setx(s.xcor() - speed)


        # approximate bounding boxes for collisions and scoring
        player_w = 10 * player.shapesize()[1]
        player_h = 10 * player.shapesize()[0]
        ob_w = getattr(s, "w", 20)
        ob_h = getattr(s, "h", 20)
        dx = abs(player.xcor() - s.xcor())
        dy = abs(player.ycor() - s.ycor())
        # score when obstacle passes the player x and hasn't been counted
        if not getattr(s, "scored", False) and s.xcor() < player.xcor():
            s.scored = True
            score += 1
            if score > high_score:
                high_score = score
            update_scoreboard()


        if s.xcor() < -420:
            s.hideturtle()
            if s in spikes:
                spikes.remove(s)
            continue


        # Collision rules by type
        collided = False
        if getattr(s, "type", "") == "ground":
            # collide if bounding boxes overlap (player touches ground spike)
            if dx < (player_w + ob_w)/2 and (player.ycor() - (-100 + ob_h/2)) < player_h/2 + ob_h/2:
                collided = True
        elif getattr(s, "type", "") == "ceiling":
            # collide if player's top is higher than ceiling's bottom while overlapping horizontally
            ceiling_bottom = s.ycor() - ob_h/2
            player_top = player.ycor() + player_h/2
            if dx < (player_w + ob_w)/2 and player_top > ceiling_bottom:
                collided = True
        elif getattr(s, "type", "") == "moving":
            # general bounding box collision
            if dx < (player_w + ob_w)/2 and dy < (player_h + ob_h)/2:
                collided = True
        else:
            # fallback using distance
            if player.distance(s) < 25:
                collided = True


        if collided:
            player.color("red")
            print("Game Over")
            time.sleep(1)
            player.color("white")
            player.goto(-300, -100)
            player.dy = 0
            player.ducking = False
            player.duck_timer = 0
            player.shapesize(1,1)
            # save high score
            try:
                with open(hs_path, "w") as f:
                    f.write(str(high_score))
            except:
                pass
            # reset obstacles
            for sp in spikes:
                sp.hideturtle()
            spikes.clear()
            spikes.append(create_ground_spike(300))
            # reset score and timers
            score = 0
            update_scoreboard()
            spawn_timer = 0
            spawn_interval = 120
            spawn_speedup_timer = 0
            break


    time.sleep(0.01) # Small delay to make it runnable
wn.mainloop()

