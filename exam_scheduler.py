"""
Name: Your Name
Student ID: 123456

Partner Name: Friend Name
Student ID: 654321
"""

import random
import math
import time
from collections import defaultdict

# -----------------------------
# DATASET (12 COURSES, 60 STUDENTS)
# -----------------------------

courses = {f"C{i}": {"instructor_preferences": [random.randint(0,5)]} for i in range(12)}

students = {
    f"S{i}": random.sample(list(courses.keys()), random.randint(2,4))
    for i in range(60)
}

rooms = {"R1": 20, "R2": 30, "R3": 50}

time_slots = [
    ("Day1","Morning"), ("Day1","Afternoon"),
    ("Day2","Morning"), ("Day2","Afternoon"),
    ("Day3","Morning"), ("Day3","Afternoon")
]

# -----------------------------
# BUILD ENROLLMENT
# -----------------------------

def build_enrollment():
    enrollment = defaultdict(int)
    for s, clist in students.items():
        for c in clist:
            enrollment[c] += 1
    return enrollment

# -----------------------------
# CHECK HARD CONSTRAINTS
# -----------------------------

def check_hard(schedule, enrollment):
    violations = 0

    # student conflict
    for s, clist in students.items():
        slots = []
        for c in clist:
            if c in schedule:
                slots.append(schedule[c][0])
        if len(slots) != len(set(slots)):
            violations += 1

    # room capacity + conflict
    used = {}
    for c, (slot, room) in schedule.items():
        if enrollment[c] > rooms[room]:
            violations += 1

        if (slot, room) in used:
            violations += 1
        used[(slot, room)] = c

    return violations

# -----------------------------
# CHECK SOFT CONSTRAINTS
# -----------------------------

def check_soft(schedule, enrollment):
    violations = 0

    for s, clist in students.items():
        day_map = defaultdict(list)

        for c in clist:
            if c in schedule:
                slot = schedule[c][0]
                day = time_slots[slot][0]
                day_map[day].append(slot)

        for slots in day_map.values():
            if len(slots) > 2:
                violations += 1

            if len(slots) > 1:
                violations += 1

    # instructor preference
    for c, (slot, room) in schedule.items():
        if slot not in courses[c]["instructor_preferences"]:
            violations += 1

    return violations

# -----------------------------
# HEURISTIC FUNCTION
# -----------------------------

def cost(schedule, enrollment):
    h = check_hard(schedule, enrollment)
    s = check_soft(schedule, enrollment)
    return (1000*h + 10*s), h, s

# -----------------------------
# RANDOM SCHEDULE
# -----------------------------

def random_schedule():
    return {
        c: (random.randint(0,5), random.choice(list(rooms.keys())))
        for c in courses
    }

# -----------------------------
# SIMULATED ANNEALING
# -----------------------------

def simulated_annealing():
    enrollment = build_enrollment()

    current = random_schedule()
    curr_cost, _, _ = cost(current, enrollment)

    best = current.copy()
    best_cost = curr_cost

    T = 100

    for _ in range(2000):
        neighbor = current.copy()
        c = random.choice(list(courses.keys()))
        neighbor[c] = (random.randint(0,5), random.choice(list(rooms.keys())))

        n_cost, _, _ = cost(neighbor, enrollment)

        if n_cost < curr_cost or random.random() < math.exp((curr_cost-n_cost)/T):
            current = neighbor
            curr_cost = n_cost

            if curr_cost < best_cost:
                best = current.copy()
                best_cost = curr_cost

        T *= 0.99

    return best, enrollment

# -----------------------------
# LAS VEGAS
# -----------------------------

def las_vegas():
    enrollment = build_enrollment()

    while True:
        schedule = {}
        success = True

        for c in courses:
            placed = False

            for _ in range(50):
                slot = random.randint(0,5)
                room = random.choice(list(rooms.keys()))

                temp = schedule.copy()
                temp[c] = (slot, room)

                if check_hard(temp, enrollment) == 0:
                    schedule[c] = (slot, room)
                    placed = True
                    break

            if not placed:
                success = False
                break

        if success:
            return schedule, enrollment

# -----------------------------
# PRINT
# -----------------------------

def print_schedule(schedule):
    for c,(slot,room) in schedule.items():
        print(f"{c} -> {time_slots[slot]} in {room}")

# -----------------------------
# RUN
# -----------------------------

# Heuristic
start = time.time()
h_sched, enroll = simulated_annealing()
end = time.time()

h_cost, h_hard, h_soft = cost(h_sched, enroll)

print("\n=== HEURISTIC (Simulated Annealing) ===")
print_schedule(h_sched)
print("Time:", (end-start)*1000,"ms")
print("Hard:", h_hard)
print("Soft:", h_soft)

# Las Vegas
start = time.time()
lv_sched, enroll = las_vegas()
end = time.time()

lv_cost, lv_hard, lv_soft = cost(lv_sched, enroll)

print("\n=== LAS VEGAS ===")
print_schedule(lv_sched)
print("Time:", (end-start)*1000,"ms")
print("Hard:", lv_hard)
print("Soft:", lv_soft)

"""
CONCLUSION:

Simulated Annealing improves schedules efficiently but may still produce
some violations. Las Vegas guarantees valid schedules but may take longer.
Thus, heuristic methods are faster, while randomized methods ensure correctness.
"""
