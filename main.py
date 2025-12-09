#!/usr/bin/env python3
import time
import threading
import queue
import random
from enum import Enum, auto

# ===== CONFIG =====
WAKEUP_LOCK = 5
IDLE_RANDOM_BEHAVIOR_AFTER = 5
IDLE_TIMEOUT = 30
SNORE_LOCK = 5
# ==================

class State(Enum):
    START = auto()
    WAKEUP = auto()
    IDLE = auto()
    SLEEPING = auto()
    SNORING = auto()

class Mood(Enum):
    HAPPY = auto()
    SAD = auto()
    ANGRY = auto()

class Priority(Enum):
    GENERIC = 3
    TOUCH = 2
    FEED = 1

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

        def finish():
            time.sleep(WAKEUP_LOCK)
            self.state = State.IDLE
            self.last_activity = time.time()
            print("[FSM] WAKEUP → IDLE")
            print("[HUNGER] resumed")
        threading.Thread(target=finish, daemon=True).start()

    def on_idle_timeout(self, payload):
        print("[FSM] Idle -> Snoring")
        print("[HUNGER] paused during sleep")
        self.state = State.SNORING
        self.lock_for(SNORE_LOCK)
        self.play("snore")
        self.anim("snore", SNORE_LOCK)

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
            action = random.choice(["cry", "weak", "sick", "cough", "vomit", "sneeze"])
            print(f"[STARVING ACTION] {action}")
            self.play(action)
            self.anim(action, 3)
            return

        elif self.hunger < 40:
            action = random.choice(["whine", "ask_food", "hungry"])
            print(f"[HUNGRY ACTION] {action}")
            self.play(action)
            self.anim(action, 3)
            return

        # Mood-based behaviors
        mood_actions = {
            Mood.HAPPY: ["look", "whistle", "laugh", "spin"],
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
            self.anim("purr", 1)

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
