import random
import math
from collections import defaultdict

# ============================================================
# EXAM SCHEDULING USING HEURISTIC FUNCTION + SIMULATED ANNEALING
# ============================================================
# Easy English version for students
#
# This program:
# 1. Reads sample data for courses, students, rooms, and time slots
# 2. Creates an initial exam schedule
# 3. Improves the schedule using Simulated Annealing
# 4. Prints the final schedule and heuristic score
# ============================================================


# ------------------------------------------------------------
# SAMPLE INPUT DATA
# You can replace these with your own real data
# ------------------------------------------------------------

courses = {
    "IT101": {
        "name": "Programming 1",
        "instructor_preferences": [0, 1]  # preferred slot indexes
    },
    "IT102": {
        "name": "Database Systems",
        "instructor_preferences": [2, 3]
    },
    "IT103": {
        "name": "Networking",
        "instructor_preferences": [1, 4]
    },
    "IT104": {
        "name": "Web Development",
        "instructor_preferences": [0, 2]
    },
    "IT105": {
        "name": "Algorithms",
        "instructor_preferences": [3, 5]
    }
}

students = {
    "S1": ["IT101", "IT102", "IT105"],
    "S2": ["IT101", "IT103"],
    "S3": ["IT102", "IT104"],
    "S4": ["IT101", "IT104", "IT105"],
    "S5": ["IT103", "IT104"],
    "S6": ["IT102", "IT103", "IT105"],
    "S7": ["IT101", "IT102"],
    "S8": ["IT104", "IT105"],
    "S9": ["IT101", "IT103", "IT104"],
    "S10": ["IT102", "IT105"]
}

rooms = {
    "R1": 40,
    "R2": 25,
    "R3": 20
}

# Time slots are stored in a list
# Index 0 means Day 1, 9:00-11:00
time_slots = [
    ("Day 1", "9:00-11:00"),
    ("Day 1", "1:00-3:00"),
    ("Day 2", "9:00-11:00"),
    ("Day 2", "1:00-3:00"),
    ("Day 3", "9:00-11:00"),
    ("Day 3", "1:00-3:00")
]


# ------------------------------------------------------------
# STEP 1: COUNT ENROLLMENT PER COURSE
# ------------------------------------------------------------
def build_course_enrollment(students):
    enrollment = defaultdict(int)
    course_students = defaultdict(set)

    for student_id, course_list in students.items():
        for course in course_list:
            enrollment[course] += 1
            course_students[course].add(student_id)

    return dict(enrollment), dict(course_students)


# ------------------------------------------------------------
# STEP 2: BUILD CONFLICT MATRIX
# This shows how many students are shared by two courses
# ------------------------------------------------------------
def build_conflict_matrix(course_students):
    course_list = list(course_students.keys())
    conflicts = defaultdict(int)

    for i in range(len(course_list)):
        for j in range(i + 1, len(course_list)):
            c1 = course_list[i]
            c2 = course_list[j]

            shared_students = len(course_students[c1] & course_students[c2])

            if shared_students > 0:
                conflicts[(c1, c2)] = shared_students
                conflicts[(c2, c1)] = shared_students

    return dict(conflicts)


# ------------------------------------------------------------
# HELPER FUNCTION:
# Check if two slots are consecutive on the same day
# ------------------------------------------------------------
def is_consecutive(slot_a, slot_b, time_slots):
    day_a, _ = time_slots[slot_a]
    day_b, _ = time_slots[slot_b]

    if day_a != day_b:
        return False

    return abs(slot_a - slot_b) == 1


# ------------------------------------------------------------
# HELPER FUNCTION:
# Compute how balanced the schedule is across days
# Lower is better
# ------------------------------------------------------------
def compute_day_load_penalty(schedule, time_slots):
    day_counts = defaultdict(int)

    for course, (slot, room) in schedule.items():
        day = time_slots[slot][0]
        day_counts[day] += 1

    all_days = sorted({day for day, time in time_slots})
    total_exams = len(schedule)
    ideal_per_day = total_exams / max(1, len(all_days))

    imbalance = 0
    for day in all_days:
        imbalance += abs(day_counts[day] - ideal_per_day)

    return imbalance


# ------------------------------------------------------------
# STEP 3: HEURISTIC EVALUATION FUNCTION
# Lower total cost = better schedule
# ------------------------------------------------------------
def evaluate_schedule(schedule, students, rooms, time_slots, courses, enrollment):
    hard_violations = 0
    same_day_excess = 0
    consecutive_exams = 0
    room_wastage = 0
    instructor_penalty = 0
    missing_assignments = 0

    # ----------------------------
    # HARD CONSTRAINT 1:
    # Each course must be assigned exactly once
    # ----------------------------
    for course in courses:
        if course not in schedule:
            missing_assignments += 1

    # ----------------------------
    # HARD CONSTRAINT 2:
    # A room cannot be used by 2 exams at the same time
    # ----------------------------
    room_usage = defaultdict(list)
    for course, (slot, room) in schedule.items():
        room_usage[(slot, room)].append(course)

    for key, course_list in room_usage.items():
        if len(course_list) > 1:
            hard_violations += (len(course_list) - 1)

    # ----------------------------
    # HARD CONSTRAINT 3:
    # Room must have enough capacity
    # SOFT CONSTRAINT:
    # Avoid wasting large rooms
    # ----------------------------
    for course, (slot, room) in schedule.items():
        room_capacity = rooms[room]
        enrolled = enrollment.get(course, 0)

        if enrolled > room_capacity:
            hard_violations += (enrolled - room_capacity)

        room_wastage += max(0, room_capacity - enrolled)

        # Instructor preference penalty
        preferred_slots = courses[course].get("instructor_preferences", [])
        if preferred_slots and slot not in preferred_slots:
            instructor_penalty += 1

    # ----------------------------
    # HARD CONSTRAINT 4:
    # A student cannot have 2 exams at the same time
    #
    # SOFT CONSTRAINTS:
    # - More than 2 exams in one day
    # - Consecutive exams
    # ----------------------------
    for student_id, course_list in students.items():
        student_slots = []
        day_groups = defaultdict(list)

        for course in course_list:
            if course in schedule:
                slot = schedule[course][0]
                student_slots.append(slot)
                day = time_slots[slot][0]
                day_groups[day].append(slot)

        # Same-time conflicts
        slot_count = defaultdict(int)
        for slot in student_slots:
            slot_count[slot] += 1

        for slot, count in slot_count.items():
            if count > 1:
                hard_violations += (count - 1)

        # Same-day excess exams and consecutive exams
        for day, slots_on_day in day_groups.items():
            if len(slots_on_day) > 2:
                same_day_excess += (len(slots_on_day) - 2)

            slots_on_day = sorted(slots_on_day)
            for i in range(len(slots_on_day) - 1):
                if is_consecutive(slots_on_day[i], slots_on_day[i + 1], time_slots):
                    consecutive_exams += 1

    hard_violations += missing_assignments

    # Balanced exam load across days
    imbalance = compute_day_load_penalty(schedule, time_slots)

    # ----------------------------
    # HEURISTIC COST FUNCTION
    # ----------------------------
    total_cost = (
        1000 * hard_violations +
        10 * same_day_excess +
        5 * consecutive_exams +
        2 * room_wastage +
        3 * instructor_penalty +
        4 * imbalance
    )

    details = {
        "hard_violations": hard_violations,
        "same_day_excess": same_day_excess,
        "consecutive_exams": consecutive_exams,
        "room_wastage": room_wastage,
        "instructor_penalty": instructor_penalty,
        "imbalance": imbalance,
        "total_cost": total_cost
    }

    return total_cost, details


# ------------------------------------------------------------
# STEP 4: CREATE INITIAL SCHEDULE (Greedy Start)
# We schedule difficult courses first
# ------------------------------------------------------------
def generate_initial_schedule(courses, students, rooms, time_slots, enrollment, conflict_matrix):
    schedule = {}

    # Use smaller rooms first to reduce room wastage
    sorted_rooms = sorted(rooms.keys(), key=lambda r: rooms[r])

    # Sort courses:
    # 1. Courses with more conflicts first
    # 2. Courses with bigger enrollment first
    course_order = sorted(
        courses.keys(),
        key=lambda c: (
            -sum(conflict_matrix.get((c, other), 0) for other in courses if other != c),
            -enrollment.get(c, 0)
        )
    )

    for course in course_order:
        best_choice = None
        best_cost = float("inf")

        for slot in range(len(time_slots)):
            for room in sorted_rooms:
                trial_schedule = schedule.copy()
                trial_schedule[course] = (slot, room)

                cost, _ = evaluate_schedule(
                    trial_schedule,
                    students,
                    rooms,
                    time_slots,
                    courses,
                    enrollment
                )

                if cost < best_cost:
                    best_cost = cost
                    best_choice = (slot, room)

        schedule[course] = best_choice

    return schedule


# ------------------------------------------------------------
# STEP 5: CREATE A NEIGHBOR SCHEDULE
# Randomly change one course's slot and room
# ------------------------------------------------------------
def random_neighbor(schedule, rooms, time_slots):
    new_schedule = schedule.copy()

    course = random.choice(list(new_schedule.keys()))
    new_slot = random.randrange(len(time_slots))
    new_room = random.choice(list(rooms.keys()))

    new_schedule[course] = (new_slot, new_room)
    return new_schedule


# ------------------------------------------------------------
# STEP 6: SIMULATED ANNEALING ALGORITHM
# ------------------------------------------------------------
def simulated_annealing(
    courses,
    students,
    rooms,
    time_slots,
    max_iterations=5000,
    initial_temp=100.0,
    cooling_rate=0.995,
    seed=42
):
    random.seed(seed)

    enrollment, course_students = build_course_enrollment(students)

    # Make sure every course exists in enrollment
    for course in courses:
        enrollment.setdefault(course, 0)
        course_students.setdefault(course, set())

    conflict_matrix = build_conflict_matrix(course_students)

    # Create starting schedule
    current_schedule = generate_initial_schedule(
        courses,
        students,
        rooms,
        time_slots,
        enrollment,
        conflict_matrix
    )

    current_cost, current_details = evaluate_schedule(
        current_schedule,
        students,
        rooms,
        time_slots,
        courses,
        enrollment
    )

    best_schedule = current_schedule.copy()
    best_cost = current_cost
    best_details = current_details.copy()

    temperature = initial_temp

    for _ in range(max_iterations):
        neighbor_schedule = random_neighbor(current_schedule, rooms, time_slots)
        neighbor_cost, neighbor_details = evaluate_schedule(
            neighbor_schedule,
            students,
            rooms,
            time_slots,
            courses,
            enrollment
        )

        delta = neighbor_cost - current_cost

        # Accept better solution
        # Or sometimes accept worse solution to escape local optimum
        if delta < 0 or random.random() < math.exp(-delta / max(temperature, 1e-9)):
            current_schedule = neighbor_schedule
            current_cost = neighbor_cost
            current_details = neighbor_details

            # Update best solution found
            if current_cost < best_cost:
                best_schedule = current_schedule.copy()
                best_cost = current_cost
                best_details = current_details.copy()

        # Cool down
        temperature *= cooling_rate

        if temperature < 0.001:
            break

    return best_schedule, best_cost, best_details, enrollment


# ------------------------------------------------------------
# STEP 7: PRINT THE FINAL RESULT
# ------------------------------------------------------------
def print_schedule(schedule, time_slots, enrollment):
    print("\nFINAL EXAM SCHEDULE")
    print("=" * 50)

    for course in sorted(schedule.keys()):
        slot, room = schedule[course]
        day, time = time_slots[slot]
        print(f"{course} -> {day}, {time}, Room {room}, Students: {enrollment[course]}")


# ------------------------------------------------------------
# MAIN PROGRAM
# ------------------------------------------------------------
if __name__ == "__main__":
    best_schedule, best_cost, best_details, enrollment = simulated_annealing(
        courses,
        students,
        rooms,
        time_slots
    )

    print("BEST HEURISTIC COST:", best_cost)
    
    print("\nCOST DETAILS:")
    for key, value in best_details.items():
        print(f"{key}: {value}")

    print_schedule(best_schedule, time_slots, enrollment)
