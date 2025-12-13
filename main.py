#!/usr/bin/env python3
import time
import threading
import queue
import json
import os, random
from enum import Enum, auto
SOUND_FOLDER = "sounds/"

def get_sound_list(prefix):
    if not os.path.exists(SOUND_FOLDER):
        print("Missing sound folder!")
        return []
    else 
        return [
            f.replace(".wav", "")
            for f in os.listdir(SOUND_FOLDER)
            if f.startswith(prefix) and f.endswith(".wav")
        ]
    
# Initialize audio files data.
SOUND_SNEEZE = get_sound_list("sneeze")
SOUND_COUGH = get_sound_list("cough")
SOUND_SICK = get_sound_list("sick")

SOUND_SNORING = get_sound_list("snoring")
SOUND_LOVE = get_sound_list("love_reply")
SOUND_LAUGH = get_sound_list("laugh")
SOUND_HUNGRY = get_sound_list("hungry")
SOUND_HOWAREYOU = get_sound_list("howareyou_reply")
SOUND_HATE_REPLY = get_sound_list("hate_reply")
SOUND_BYE = get_sound_list("bye")
SOUND_GREETING_MORNING = get_sound_list("greeting_morning")
SOUND_GREETING_AFTERNOON = get_sound_list("greeting_afternoon")
SOUND_GREETING_EVENING = get_sound_list("greeting_evening")
SOUND_GREETING_NIGHT = get_sound_list("greeting_night")
SOUND_RANDOM = get_sound_list("random")

def get_time_greeting():
    hour = time.localtime().tm_hour

    if 5 <= hour < 12:
        return random.choice(SOUND_GREETING_MORNING)
    elif 12 <= hour < 17:
        return random.choice(SOUND_GREETING_AFTERNOON)
    elif 17 <= hour < 21:
        return random.choice(SOUND_GREETING_EVENING)
    else:
        return random.choice(SOUND_GREETING_NIGHT)


# ===== CONFIG =====
WAKEUP_LOCK = 5
IDLE_RANDOM_BEHAVIOR_AFTER = 5
IDLE_TIMEOUT = 30
SNORE_LOCK = 5
LISTENING_LOCK = 5
NORMAL_LOCK = 5
# ==================

class State(Enum):
    START = auto()
    WAKEUP = auto()
    IDLE = auto()
    SLEEPING = auto()
    SNORING = auto()
    LISTENING = auto()
    BUSY = auto()

class Mood(Enum):
    HAPPY = auto()
    SAD = auto()
    ANGRY = auto()

class Priority(Enum):
    GENERIC = 3
    TOUCH = 2
    FEED = 1
    WAKEWORD = 0

class Event:
    def __init__(self, priority, name, payload=None):
        self.priority = priority
        self.name = name
        self.payload = payload or {}

class FurbyFSM:
    def __init__(self):
        self.event_counter = 0
        self.state = State.START
        self.event_q = queue.PriorityQueue()

        self.locked_until = 0
        self.last_activity = time.time()
        self.running = True

        # ===== HUNGER SYSTEM =====
        self.hunger = 100
        self.last_hunger_tick = time.time()

        # ===== MOOD SYSTEM =====
        self.mood = Mood.HAPPY      # Default mood
        self.last_interaction = time.time()

        # Start main loop
        threading.Thread(target=self.main_loop, daemon=True).start()

        # Start wake sequence
        self.post(Event(Priority.GENERIC.value, "start"))

        # Random behavior system
        threading.Thread(target=self.random_behavior_watch, daemon=True).start()

        # Idle timeout watcher
        threading.Thread(target=self.idle_sleep_watch, daemon=True).start()

        # Hunger watcher
        threading.Thread(target=self.hunger_watch, daemon=True).start()
        
        #wake word listener
        threading.Thread(target=self.wakeword_listener, daemon=True).start()

    # ---- Hardware/action stubs ----
    def play(self, sound):
        print(f"[PLAY] {sound}")

    def anim(self, name, d=1):
        print(f"[ANIM] {name} ({d}s)")
        time.sleep(d)

    # ---- Utility ----   
    #def post(self, ev):
    #    self.event_q.put((ev.priority, time.time(), ev))

    def post(self, ev):
        self.event_counter += 1
        self.event_q.put((ev.priority, self.event_counter, ev))
    

    def lock_for(self, sec):
        self.locked_until = time.time() + sec
        print(f"[LOCK] locked for {sec}s")

    def locked(self):
        return time.time() < self.locked_until

    # ---- Watchers ----
    def random_behavior_watch(self):
        while self.running:
            if self.state == State.IDLE:
                if time.time() - self.last_activity > IDLE_RANDOM_BEHAVIOR_AFTER:
                    self.post(Event(Priority.GENERIC.value, "random"))
            time.sleep(5)

    def idle_sleep_watch(self):
        while self.running:
            if self.state == State.IDLE:
                if time.time() - self.last_activity > IDLE_TIMEOUT:
                    self.post(Event(Priority.GENERIC.value, "idle_timeout"))
            time.sleep(5)

    # ===== HUNGER WATCHER =====
    def hunger_watch(self):
        while self.running:
            if self.state == State.SLEEPING:
                time.sleep(5)
                continue

            if time.time() - self.last_hunger_tick > 60:  # Every 1 min
                self.hunger = max(0, self.hunger - 10)
                self.last_hunger_tick = time.time()
                print(f"[HUNGER] level = {self.hunger}")

            time.sleep(5)

    def wakeword_listener(self):
        while self.running:
            # Wake word allowed ONLY in IDLE state
            if self.state == State.IDLE:
                detected = self.detect_wakeword()
                if detected:
                    print("[WAKEWORD] wake word detected! Listening for command.")
                    #self.state = State.LISTENING
                    self.post(Event(Priority.WAKEWORD.value, "listening"))
                    time.sleep(1)  # prevent spamming
            else:
                time.sleep(0.5)

    def on_listening(self, payload):
        if self.state == State.IDLE:
            print("[FSM] IDLE → LISTENING")
            self.state = State.LISTENING
            self.lock_for(LISTENING_LOCK)
            self.play("listening")
            self.anim("listening", LISTENING_LOCK)
            
            def on_listening_completed():
                self.state = State.BUSY
                self.last_activity = time.time()
                print("[FSM] LISTENING → BUSY")
                
                data = {
                        "intent": "SINGASONG",
                        "slots": {
                            "song": "golden"
                            }
                        }
                self.process_command(data)
            threading.Thread(target=on_listening_completed, daemon=True).start()
        else: 
            print(f"Cannot listen in {self.state} state.")

    def detect_wakeword(self):
        # TODO: connect real wake-word engine here
        # For testing, we simulate random detection:
        return True

    def process_command(self, data):
        intent =  data["intent"]
        slots = data.get("slots", {})

        match intent:
            case "SINGASONG":
                self.on_singasong(slots.get("song"))

            case "GOTOSLEEP":
                self.on_gotosleep()

            case "WAKEUP":
                self.on_wakeup()

            case "TELLAJOKE":
                self.on_tellajoke()

            case "TELLASTORY":
                self.on_tellastory()

            case "TELLTIME":
                self.on_telltime()

            case "TELLDATE":
                self.on_telldate()

            case "PLAYGAME":
                self.on_playgame()

            case "SINGRHYME":
                self.on_singrhyme()

            case "DANCE":
                self.on_dance()

            case "ILOVEYOU":
                self.on_iloveyou()

            case "IHATEYOU":
                self.on_ihateyou()

            case "WHATISYOURNAME":
                self.on_what_is_your_name()

            case "WHOAREYOU":
                self.on_who_are_you()

            case "HOWAREYOU":
                self.on_how_are_you()

            case "COUNT":
                self.on_count(slots.get("number"))      # number comes from slot $pv.TwoDigitInteger

            case "SAYABC":
                self.on_sayabc()

            case "TEACHME":
                self.on_teachme()

            case "MOUTH":
                self.on_mouth(slots.get("mouthState"))

            case "TELLANUMBER":
                self.on_tell_a_number()

            case "AREYOUHUNGRY":
                self.on_are_you_hungry()

            case "MOVEEARS":
                self.on_move_ears()

            case "EYES":
                self.on_eyes(slots.get("eyeState"))

            case "LOOK":
                self.on_look(slots.get("lookState"))

            case "HEYFURBY":
                self.on_hey_furby()

            case "BYE":
                self.on_bye()

            case "GREETING":
                self.on_greeting(slots.get("greetingState"))

            case "ALARM":
                hour = slots.get("hour")
                minute = slots.get("minute")
                ampm = slots.get("ampm")
                self.on_alarm(hour, minute, ampm)  # slots: hour, minute, ampm

            case "PLAYMUSIC":
                self.on_playmusic()

            case "TELLAGE":
                self.on_tell_age()

            case "OK":
                self.on_ok()

            case "YES":
                self.on_yes()

            case "NO":
                self.on_no()

            case "CANCEL":
                self.on_cancel()

            case "REMOVEALARM":
                alarm = slots.get("alarm")
                self.on_remove_alarm(alarm)   # alarm = SingleDigitInteger

            case "TELLALARM":
                self.on_tell_alarm()

            case "FRIEND":
                self.on_friend()

            case _:
                self.on_unknown_intent(intent)

    # ============ INTENT HANDLERS ============

    def on_singasong(self, song):
        print(f"[INTENT] Sing a song: {song}")
        self.state = State.BUSY
        self.play(song)
        self.anim(song, WAKEUP_LOCK)
        
        def finish():
            self.state = State.IDLE
            self.last_activity = time.time()
            print("[FSM] BUSY → IDLE")
        threading.Thread(target=finish, daemon=True).start()

    def on_gotosleep(self):
        print("[INTENT] Go to sleep")

    def on_wakeup(self):
        print("[INTENT] Wake up")

    def on_tellajoke(self):
        print("[INTENT] Tell a joke")

    def on_tellastory(self):
        print("[INTENT] Tell a story")

    def on_telltime(self):
        print("[INTENT] Tell the time")

    def on_telldate(self):
        print("[INTENT] Tell the date")

    def on_playgame(self):
        print("[INTENT] Play a game")

    def on_singrhyme(self):
        print("[INTENT] Sing a rhyme / poem")

    def on_dance(self):
        print("[INTENT] Dance")

    def on_iloveyou(self):
        print("[INTENT] I love you")

    def on_ihateyou(self):
        print("[INTENT] I hate you")

    def on_what_is_your_name(self):
        print("[INTENT] What is your name")

    def on_who_are_you(self):
        print("[INTENT] Who are you")

    def on_how_are_you(self):
        print("[INTENT] How are you")

    def on_count(self, number):
        print(f"[INTENT] Count to {number}")

    def on_sayabc(self):
        print("[INTENT] Say ABC")

    def on_teachme(self):
        print("[INTENT] Teach me something")

    def on_mouth(self, mouthState):
        print(f"[INTENT] Mouth control: {mouthState}")

    def on_tell_a_number(self):
        print("[INTENT] Tell a number")

    def on_are_you_hungry(self):
        print("[INTENT] Are you hungry?")

    def on_move_ears(self):
        print("[INTENT] Move ears")

    def on_eyes(self, eyeState):
        print(f"[INTENT] Eyes: {eyeState}")

    def on_look(self, lookState):
        print(f"[INTENT] Look: {lookState}")

    def on_hey_furby(self):
        print("[INTENT] Hey Furby")

    def on_bye(self):
        print("[INTENT] Bye")

    def on_greeting(self,greetingState):
        print(f"[INTENT] Greeting: {greetingState}")

    def on_alarm(self, hour, minute, ampm):
        print(f"[INTENT] Alarm set for {hour}:{minute} {ampm}")

    def on_playmusic(self):
        print("[INTENT] Play music")

    def on_tell_age(self):
        print("[INTENT] Tell age")

    def on_ok(self):
        print("[INTENT] OK")

    def on_yes():
        print("[INTENT] YES")

    def on_no(self):
        print("[INTENT] NO")

    def on_cancel(self):
        print("[INTENT] CANCEL")

    def on_remove_alarm(self, alarm):
        print(f"[INTENT] Remove alarm {alarm}")

    def on_tell_alarm(self):
        print("[INTENT] Tell all alarms")

    def on_friend(self):
        print("[INTENT] Friend request")

    def on_unknown_intent(self, intent):
        print(f"[ERROR] Unknown intent: {intent}")
    

    # ---- MAIN LOOP ----
    def main_loop(self):
        while self.running:
            try:
                pr, ts, ev = self.event_q.get(timeout=0.5)
            except queue.Empty:
                continue

            if self.locked():
                print(f"[IGNORE] event {ev.name} (locked)")
                continue

            handler = getattr(self, f"on_{ev.name}", None)
            if handler:
                handler(ev.payload)
            else:
                print(f"[WARN] no handler for {ev.name}")

    # ---- MOOD SETTERS ----
    def set_mood(self, mood):
        if mood != self.mood:
            print(f"[MOOD] {self.mood.name} → {mood.name}")
        self.mood = mood
        self.last_interaction = time.time()

    # ---- HANDLERS ----
    def on_start(self, payload):
        print("[FSM] START → WAKEUP")
        self.state = State.WAKEUP
        self.lock_for(WAKEUP_LOCK)
        self.play("yawn")
        self.anim("yawn", WAKEUP_LOCK)
        
        #Play greetings
        action = get_time_greeting()
        self.play(action)
        self.anim(action, NORMAL_LOCK)

        def finish():
            time.sleep(WAKEUP_LOCK)
            self.state = State.IDLE
            self.last_activity = time.time()
            print("[FSM] WAKEUP → IDLE")
            print("[HUNGER] resumed")
        threading.Thread(target=finish, daemon=True).start()

    def on_idle_timeout(self, payload):
        print("[FSM] Idle -> Snoring")
        self.state = State.SNORING
        self.lock_for(SNORE_LOCK)
        action = random.choice(SOUND_SNORING)
        self.play(action)
        self.anim(action, SNORE_LOCK)

        def finishSnoring():
            self.state = State.SLEEPING
            print("[FSM] Snoring -> Sleeping")
        threading.Thread(target=finishSnoring, daemon=True).start()

    # ===== RANDOM BEHAVIOR WITH MOOD =====
    def on_random(self, payload):
        if self.state != State.IDLE:
            return

        # Hunger overrides mood
        if self.hunger < 20:
            action = random.choice(SOUND_SNEEZE + SOUND_COUGH + SOUND_SICK)
            print(f"[STARVING ACTION] {action}")
            self.play(action)
            self.anim(action, 3)
            return

        elif self.hunger < 40:
            action = random.choice(SOUND_HUNGRY)
            print(f"[HUNGRY ACTION] {action}")
            self.play(action)
            self.anim(action, 3)
            return

        # Mood-based behaviors
        mood_actions = {
            Mood.HAPPY: SOUND_RANDOM,
            Mood.SAD: ["sigh", "slow_blink"],
            Mood.ANGRY: ["grr", "shake_head"],
        }

        c = random.choice(mood_actions[self.mood])
        #print(f"[RANDOM] ({self.mood.name}) → {c}")
        self.play(c)
        self.anim(c, 3)

    def on_wake(self, payload):
        if self.state == State.SLEEPING:
            print("[FSM] WAKING FROM SLEEP → WAKEUP")
            self.on_start({})
        else:
            print("[INFO] Already awake")

    # ===== MOOD-DRIVEN TOUCH EVENTS =====
    def on_touch_head(self, payload):
        print("[EVENT] head touch")
        self.set_mood(Mood.HAPPY)

        if self.state == State.SLEEPING:
            self.on_wake({})
            return

        if self.state == State.IDLE:
            self.last_activity = time.time()
            self.play("purr")
            self.anim("purr", 3)

    def on_touch_belly(self, payload):
        print("[EVENT] belly touch")
        self.set_mood(Mood.HAPPY)

        if self.state == State.SLEEPING:
            self.on_wake({})
            return

        if self.state == State.IDLE:
            self.last_activity = time.time()
            self.play("giggle")
            self.anim("giggle", 1)

    def on_feed(self, payload):
        print("[EVENT] feeding")

        self.hunger = min(100, self.hunger + 40)
        print(f"[HUNGER] restored → {self.hunger}")

        if self.state == State.IDLE:
            self.last_activity = time.time()
            self.play("eat")
            self.anim("eat", 2)

    def on_tilt(self, payload):
        print("[EVENT] tilt")
        self.set_mood(Mood.SAD)

        if self.state == State.SLEEPING:
            self.on_wake({})
            return

        if self.state == State.IDLE:
            self.play("tilt")
            self.anim("tilt", 1)
            self.last_activity = time.time()

    def on_shake(self, payload):
        print("[EVENT] shake")
        self.set_mood(Mood.ANGRY)

        if self.state == State.SLEEPING:
            self.on_wake({})
            return

        if self.state == State.IDLE:
            self.play("shake")
            self.anim("shake", 1)
            self.last_activity = time.time()

    # ===== DANCE MODE =====
    def on_dance(self, payload):
        print("[EVENT] dance mode!")
        self.state = State.IDLE
        self.last_activity = time.time()
        self.play("dance")
        self.anim("dance", 10)

    def stop(self):
        self.running = False


# ============================
#     MANUAL COMMANDS
# ============================

fsm = FurbyFSM()

def event_wake(): fsm.post(Event(Priority.GENERIC.value, "wake"))
def event_touch_head(): fsm.post(Event(Priority.TOUCH.value, "touch_head"))
def event_touch_belly(): fsm.post(Event(Priority.TOUCH.value, "touch_belly"))
def event_feed(): fsm.post(Event(Priority.FEED.value, "feed"))
def event_tilt(): fsm.post(Event(Priority.TOUCH.value, "tilt"))
def event_shshake(): fsm.post(Event(Priority.TOUCH.value, "shake"))
def event_dance(): fsm.post(Event(Priority.TOUCH.value, "dance"))
def event_wakeword(): fsm.post(Event(Priority.WAKEWORD.value, "listening"))
# ============================
# CONSOLE INPUT LOOP
# ============================
def console_loop():
    while True:
        cmd = input("> ").strip()

        if cmd == "wake": event_wake()
        elif cmd == "head": event_touch_head()
        elif cmd == "belly": event_touch_belly()
        elif cmd == "feed": event_feed()
        elif cmd == "tilt": event_tilt()
        elif cmd == "shake": event_shshake()
        elif cmd == "dance": event_dance()
        elif cmd == "wakeword": event_wakeword()
        elif cmd == "exit": break
        else:
            print("Commands: wake, head, belly, feed, tilt, shake, dance")

threading.Thread(target=console_loop, daemon=True).start()

# Keep alive
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    fsm.stop()
