#!/usr/bin/env python3
"""
Smart Task Prioritizer

A task management app that goes beyond a simple to-do list.
Each task gets a real priority score based on its deadline,
how important it is, and how long it will take to complete.

The score updates automatically every time you run the script,
so tasks naturally become more urgent as their deadlines approach.

Usage:
    python to do list.py

Author:
    BY ST GROUP 1
"""

import json
import os
import sys
import math
import logging
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass, field, asdict


# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS — tweak these to match your preferences
# ─────────────────────────────────────────────────────────────────────────────

TASKS_FILE: str = "tasks.json"          # where your tasks are saved
CRITICAL_SCORE_THRESHOLD: float = 75.0  # above this = red alert territory
DATE_FORMAT: str = "%Y-%m-%d"           # all dates follow this pattern


# Terminal colors — nothing fancy, just makes the output easier to read
class Color:
    RESET     = "\033[0m"
    BOLD      = "\033[1m"
    DIM       = "\033[2m"
    RED       = "\033[91m"
    YELLOW    = "\033[93m"
    GREEN     = "\033[92m"
    CYAN      = "\033[96m"
    MAGENTA   = "\033[95m"
    BLUE      = "\033[94m"
    WHITE     = "\033[97m"
    BG_RED    = "\033[41m"
    BG_YELLOW = "\033[43m"


# Simple logger so we know what's happening behind the scenes
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# TASK — the core data structure
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Task:
    """A single task with everything we need to prioritize it.

    Args:
        task_id: Unique number that identifies this task.
        title: Short name for the task.
        description: More details about what needs to be done.
        deadline: Due date in YYYY-MM-DD format.
        importance: How important is this? Scale of 1 (meh) to 10 (critical).
        complexity: Rough estimate of how many hours this will take (1–100).
        category: A label like 'Work', 'Personal', 'Health', etc.
        completed: Is this task done? Defaults to False.
        created_at: Timestamp set automatically when the task is created.
        priority_score: The calculated urgency score (0–100). Updated dynamically.
        quadrant: Which Eisenhower quadrant this task falls into.
    """

    task_id: int
    title: str
    description: str
    deadline: str
    importance: int
    complexity: int
    category: str
    completed: bool = False
    created_at: str = field(
        default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    priority_score: float = 0.0
    quadrant: str = ""

    def __post_init__(self):
        """Runs right after the task is created — validates fields and scores it."""
        self._validate_fields()
        self.refresh_score()

    def _validate_fields(self) -> None:
        """Makes sure the task data actually makes sense before we save it.

        Raises:
            ValueError: If something looks wrong (empty title, bad date, etc.)
        """
        if not self.title or not self.title.strip():
            raise ValueError("Task title can't be empty.")

        if not (1 <= self.importance <= 10):
            raise ValueError(
                f"Importance must be between 1 and 10. Got: {self.importance}"
            )

        if not (1 <= self.complexity <= 100):
            raise ValueError(
                f"Complexity must be between 1 and 100 hours. Got: {self.complexity}"
            )

        # make sure the date is real and formatted correctly
        try:
            datetime.strptime(self.deadline, DATE_FORMAT)
        except ValueError as exc:
            raise ValueError(
                f"Bad date format: '{self.deadline}'. "
                f"Please use {DATE_FORMAT} (e.g. 2025-12-31)."
            ) from exc

    def refresh_score(self) -> None:
        """Recalculates the priority score and Eisenhower quadrant.

        Call this whenever you need an up-to-date score — we run it
        automatically on startup so scores never go stale.
        """
        self.priority_score = calculate_priority_score(
            deadline=self.deadline,
            importance=self.importance,
            complexity=self.complexity,
        )
        self.quadrant = self._determine_quadrant()

    def _determine_quadrant(self) -> str:
        """Figures out which Eisenhower quadrant this task belongs to.

        The 2x2 matrix is based on two questions:
          - Is it urgent? (deadline soon OR score is critical)
          - Is it important? (importance >= 7)

        Returns:
            The quadrant label as a readable string.
        """
        days_left = _days_until_deadline(self.deadline)
        is_urgent    = days_left <= 3 or self.priority_score >= CRITICAL_SCORE_THRESHOLD
        is_important = self.importance >= 7

        if is_urgent and is_important:
            return "Q1 — Do it now (Critical)"
        elif not is_urgent and is_important:
            return "Q2 — Schedule it (Important)"
        elif is_urgent and not is_important:
            return "Q3 — Delegate it (Urgent)"
        else:
            return "Q4 — Drop it (Low value)"

    def to_dict(self) -> dict:
        """Turns the task into a plain dictionary so we can save it as JSON.

        Returns:
            A dict with all the task's fields.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        """Rebuilds a Task object from a dictionary (e.g. loaded from JSON).

        We only pick the fields we know about, so old or extra keys
        in the file won't cause a crash.

        Args:
            data: Dictionary containing the task fields.

        Returns:
            A fresh Task instance with a recalculated score.
        """
        known_fields = {
            "task_id", "title", "description", "deadline",
            "importance", "complexity", "category", "completed", "created_at",
        }
        filtered = {k: v for k, v in data.items() if k in known_fields}
        task = cls(**filtered)
        task.refresh_score()
        return task

    def __repr__(self) -> str:
        return (
            f"Task(id={self.task_id}, title='{self.title}', "
            f"score={self.priority_score:.1f}, quadrant='{self.quadrant}')"
        )


# ─────────────────────────────────────────────────────────────────────────────
# PRIORITY SCORE ENGINE — the heart of the app
# ─────────────────────────────────────────────────────────────────────────────

def _days_until_deadline(deadline_str: str) -> float:
    """Simple helper: how many days until (or since) a deadline?

    Args:
        deadline_str: A date string in YYYY-MM-DD format.

    Returns:
        Number of days remaining. Negative means it's already overdue.
    """
    deadline_date = datetime.strptime(deadline_str, DATE_FORMAT).date()
    return (deadline_date - date.today()).days


def calculate_priority_score(
    deadline: str,
    importance: int,
    complexity: int,
) -> float:
    """Calculates a single urgency score (0–100) for a task.

    Instead of just sorting by deadline, this combines three things:

    1. Deadline pressure (40% of the score)
       How much time is left? The closer the deadline,
       the higher this component gets. We use an exponential
       curve for the last 7 days so the score spikes sharply
       when a deadline is right around the corner.

    2. Importance (35% of the score)
       Straightforward — a task rated 10/10 scores higher
       than one rated 3/10.

    3. Complexity (25% of the score)
       Heavier tasks need attention earlier. We use a logarithmic
       scale so a 40h task isn't absurdly boosted compared to a 20h one.

    Final formula:
        score = (0.40 × deadline) + (0.35 × importance) + (0.25 × complexity)

    Args:
        deadline: Due date in YYYY-MM-DD format.
        importance: Task importance from 1 to 10.
        complexity: Estimated hours of work, from 1 to 100.

    Returns:
        A float between 0.0 and 100.0.
    """

    # --- Part 1: Deadline pressure -------------------------------------------
    days_left = _days_until_deadline(deadline)

    if days_left < 0:
        # already overdue — max urgency, no discussion
        deadline_score = 100.0

    elif days_left == 0:
        # due today — also maxed out
        deadline_score = 100.0

    elif days_left <= 7:
        # exponential spike: urgency jumps fast in the last week
        deadline_score = 100.0 * math.exp(-0.05 * days_left)

    elif days_left <= 30:
        # gentle linear decline over the next few weeks
        deadline_score = max(0.0, 75.0 - (days_left - 7) * 3.26)

    else:
        # far away — low baseline score, barely on the radar
        deadline_score = max(0.0, 10.0 - (days_left - 30) * 0.1)

    deadline_score = min(deadline_score, 100.0)

    # --- Part 2: Importance ---------------------------------------------------
    # simple normalization: 1→10, 10→100
    importance_score = (importance / 10.0) * 100.0

    # --- Part 3: Complexity ---------------------------------------------------
    # log scale: 1h→0, 100h→100 — prevents huge tasks from dominating
    complexity_score = (math.log2(complexity) / math.log2(100)) * 100.0

    # --- Combine everything with weights -------------------------------------
    final_score = (
        0.40 * deadline_score
        + 0.35 * importance_score
        + 0.25 * complexity_score
    )

    return round(min(final_score, 100.0), 2)


# ─────────────────────────────────────────────────────────────────────────────
# TASK MANAGER — handles all the CRUD logic and file storage
# ─────────────────────────────────────────────────────────────────────────────

class TaskManager:
    """Manages the full list of tasks — loading, saving, adding, deleting, etc.

    Think of this as the backend of the app. It doesn't care about
    how things look on screen — that's the CLI's job.

    Args:
        tasks_file: Path to the JSON file where tasks are stored.
    """

    def __init__(self, tasks_file: str = TASKS_FILE):
        self.tasks_file = tasks_file
        self.tasks: list[Task] = []
        self._next_id: int = 1
        self._load_tasks()

    # ── Loading and saving ────────────────────────────────────────────────────

    def _load_tasks(self) -> None:
        """Reads tasks from the JSON file into memory.

        If the file doesn't exist yet, we just start fresh — no problem.
        Scores are recalculated on load so they always reflect today's date.
        """
        if not os.path.exists(self.tasks_file):
            logger.info("No data file found. Starting with an empty list.")
            return

        try:
            with open(self.tasks_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            if not isinstance(raw_data, list):
                raise ValueError("JSON root must be a list.")

            loaded_count = 0
            for item in raw_data:
                try:
                    task = Task.from_dict(item)
                    self.tasks.append(task)
                    loaded_count += 1
                except (ValueError, KeyError, TypeError) as e:
                    # skip broken entries but keep going
                    logger.warning(
                        "Skipping invalid task '%s': %s",
                        item.get("title", "?"), e
                    )

            self._recalculate_next_id()
            logger.info(
                "Loaded %d task(s) from '%s'. Scores refreshed for today.",
                loaded_count, self.tasks_file
            )

        except json.JSONDecodeError as e:
            logger.error("Corrupted JSON file: %s. Starting fresh.", e)
            self.tasks = []
        except OSError as e:
            logger.error("Couldn't read '%s': %s", self.tasks_file, e)
            self.tasks = []

    def save_tasks(self) -> bool:
        """Writes all tasks to the JSON file safely.

        We write to a temporary file first, then swap it in.
        This way, if something goes wrong mid-write, your data isn't lost.

        Returns:
            True if it worked, False if something went wrong.
        """
        temp_file = self.tasks_file + ".tmp"
        try:
            data = [task.to_dict() for task in self.tasks]
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

            # atomic swap — replaces the old file in one step
            os.replace(temp_file, self.tasks_file)
            logger.info("Saved %d task(s) to '%s'.", len(self.tasks), self.tasks_file)
            return True

        except OSError as e:
            logger.error("Save failed: %s", e)
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False

    def _recalculate_next_id(self) -> None:
        """Figures out what the next task ID should be based on existing tasks."""
        if self.tasks:
            self._next_id = max(t.task_id for t in self.tasks) + 1
        else:
            self._next_id = 1

    # ── CRUD operations ───────────────────────────────────────────────────────

    def add_task(
        self,
        title: str,
        description: str,
        deadline: str,
        importance: int,
        complexity: int,
        category: str = "General",
    ) -> Task:
        """Creates a new task and adds it to the list.

        Args:
            title: What the task is called.
            description: More detail about what needs to be done.
            deadline: Due date as YYYY-MM-DD.
            importance: How important is it? (1–10)
            complexity: How many hours will it take? (1–100)
            category: Optional label like 'Work' or 'Personal'.

        Returns:
            The newly created Task object.

        Raises:
            ValueError: If any of the inputs are invalid.
        """
        task = Task(
            task_id=self._next_id,
            title=title,
            description=description,
            deadline=deadline,
            importance=importance,
            complexity=complexity,
            category=category,
        )
        self.tasks.append(task)
        self._next_id += 1
        self.save_tasks()
        logger.info(
            "Added task: '%s' (ID: %d, Score: %.1f)",
            title, task.task_id, task.priority_score
        )
        return task

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Looks up a task by its ID.

        Args:
            task_id: The unique task identifier.

        Returns:
            The matching Task, or None if not found.
        """
        return next((t for t in self.tasks if t.task_id == task_id), None)

    def complete_task(self, task_id: int) -> bool:
        """Marks a task as done.

        Args:
            task_id: ID of the task to complete.

        Returns:
            True if it was found and marked, False otherwise.
        """
        task = self.get_task_by_id(task_id)
        if task:
            task.completed = True
            self.save_tasks()
            logger.info("Task ID %d marked as complete.", task_id)
            return True
        logger.warning("Task ID %d not found.", task_id)
        return False

    def delete_task(self, task_id: int) -> bool:
        """Permanently removes a task from the list.

        Args:
            task_id: ID of the task to delete.

        Returns:
            True if deleted, False if the task wasn't found.
        """
        original_count = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

        if len(self.tasks) < original_count:
            self.save_tasks()
            logger.info("Task ID %d deleted.", task_id)
            return True

        logger.warning("Task ID %d not found for deletion.", task_id)
        return False

    def refresh_all_scores(self) -> None:
        """Recalculates priority scores for every active task.

        Useful at startup (so scores reflect today's date)
        or any time you want to force a manual refresh.
        """
        for task in self.tasks:
            task.refresh_score()
        logger.info("Refreshed scores for %d task(s).", len(self.tasks))

    # ── Queries and filters ───────────────────────────────────────────────────

    def get_active_tasks(self, sort_by_score: bool = True) -> list[Task]:
        """Returns all tasks that aren't done yet.

        Args:
            sort_by_score: If True (default), most urgent tasks come first.

        Returns:
            List of active Task objects.
        """
        active = [t for t in self.tasks if not t.completed]
        if sort_by_score:
            active.sort(key=lambda t: t.priority_score, reverse=True)
        return active

    def get_critical_tasks(self) -> list[Task]:
        """Returns tasks that have crossed the critical score threshold.

        Returns:
            List of Task objects with score >= CRITICAL_SCORE_THRESHOLD.
        """
        return [
            t for t in self.get_active_tasks()
            if t.priority_score >= CRITICAL_SCORE_THRESHOLD
        ]

    def get_overdue_tasks(self) -> list[Task]:
        """Returns tasks whose deadlines have already passed.

        Returns:
            List of overdue Task objects.
        """
        return [
            t for t in self.get_active_tasks()
            if _days_until_deadline(t.deadline) < 0
        ]

    def get_tasks_by_quadrant(self) -> dict[str, list[Task]]:
        """Groups all active tasks by their Eisenhower quadrant.

        Returns:
            A dict mapping quadrant name → list of tasks in that quadrant.
        """
        quadrants: dict[str, list[Task]] = {}
        for task in self.get_active_tasks():
            quadrants.setdefault(task.quadrant, []).append(task)
        return quadrants

    def get_statistics(self) -> dict:
        """Computes a quick summary of where things stand.

        Returns:
            A dict with counts and averages across all tasks.
        """
        all_tasks = self.tasks
        active    = self.get_active_tasks()
        critical  = self.get_critical_tasks()
        overdue   = self.get_overdue_tasks()

        avg_score = (
            sum(t.priority_score for t in active) / len(active) if active else 0.0
        )

        return {
            "total":           len(all_tasks),
            "active":          len(active),
            "completed":       len(all_tasks) - len(active),
            "critical":        len(critical),
            "overdue":         len(overdue),
            "avg_score":       round(avg_score, 2),
            "completion_rate": round(
                ((len(all_tasks) - len(active)) / len(all_tasks) * 100)
                if all_tasks else 0,
                1
            ),
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI — everything the user actually sees and interacts with
# ─────────────────────────────────────────────────────────────────────────────

class CLI:
    """The command-line interface for Smart Task Prioritizer.

    Handles all screen output, menus, forms, alerts, and user input.
    Completely separate from the data logic — it just talks to TaskManager.

    Args:
        manager: The TaskManager instance to work with.
    """

    # menu items in display order
    MENU_OPTIONS = {
        "1": "Show Dashboard",
        "2": "Add a Task",
        "3": "Complete a Task",
        "4": "Delete a Task",
        "5": "Eisenhower Matrix View",
        "6": "Statistics",
        "7": "Refresh Scores",
        "0": "Quit",
    }

    def __init__(self, manager: TaskManager):
        self.manager = manager

    # ── Small display helpers ─────────────────────────────────────────────────

    @staticmethod
    def _clear_screen() -> None:
        """Clears the terminal screen (works on both Windows and Unix)."""
        os.system("cls" if os.name == "nt" else "clear")

    @staticmethod
    def _print_separator(char: str = "─", width: int = 80, color: str = Color.DIM) -> None:
        """Prints a horizontal divider line."""
        print(f"{color}{char * width}{Color.RESET}")

    @staticmethod
    def _score_color(score: float) -> str:
        """Returns the right color code for a given priority score.

        Red = critical, Yellow = medium, Cyan = low, Green = relaxed.
        """
        if score >= CRITICAL_SCORE_THRESHOLD:
            return Color.RED
        elif score >= 50.0:
            return Color.YELLOW
        elif score >= 25.0:
            return Color.CYAN
        else:
            return Color.GREEN

    @staticmethod
    def _score_bar(score: float, width: int = 15) -> str:
        """Draws a small ASCII progress bar for a score.

        Args:
            score: A value from 0 to 100.
            width: How many characters wide the bar should be.

        Returns:
            A colored bar like: ██████░░░░░░░░░
        """
        filled = int((score / 100.0) * width)
        empty  = width - filled
        color  = CLI._score_color(score)
        return f"{color}{'█' * filled}{Color.DIM}{'░' * empty}{Color.RESET}"

    @staticmethod
    def _format_deadline(deadline_str: str) -> str:
        """Shows the deadline in a human-friendly way with a color hint.

        Args:
            deadline_str: Date in YYYY-MM-DD format.

        Returns:
            Something like '🔥 2 days left' or '⚠ OVERDUE 3d'.
        """
        days = _days_until_deadline(deadline_str)
        if days < 0:
            return f"{Color.RED}⚠ OVERDUE {abs(days)}d{Color.RESET}"
        elif days == 0:
            return f"{Color.RED}⚡ TODAY{Color.RESET}"
        elif days <= 3:
            return f"{Color.YELLOW}🔥 {days}d left{Color.RESET}"
        elif days <= 7:
            return f"{Color.CYAN}⏰ {days}d left{Color.RESET}"
        else:
            return f"{Color.GREEN}📅 {days}d left{Color.RESET}"

    # ── Alert system ──────────────────────────────────────────────────────────

    def _display_critical_alerts(self) -> None:
        """Shows a big warning banner if any tasks are critical or overdue.

        This runs at the top of the dashboard so you can't miss it.
        """
        critical_tasks = self.manager.get_critical_tasks()
        overdue_tasks  = self.manager.get_overdue_tasks()

        # nothing to alert about — skip quietly
        if not critical_tasks and not overdue_tasks:
            return

        self._print_separator("═", 80, Color.RED)
        print(f"{Color.BG_RED}{Color.BOLD}  🚨  SYSTEM ALERT — CRITICAL TASKS DETECTED  🚨  {Color.RESET}")
        self._print_separator("═", 80, Color.RED)

        if overdue_tasks:
            print(f"\n{Color.RED}{Color.BOLD}  📛 OVERDUE TASKS ({len(overdue_tasks)}):{Color.RESET}")
            for task in overdue_tasks:
                days_late = abs(_days_until_deadline(task.deadline))
                print(
                    f"    {Color.RED}▶ [{task.task_id:03d}] {task.title} "
                    f"— {days_late} day(s) late "
                    f"(Score: {task.priority_score:.1f}/100){Color.RESET}"
                )

        # show critical tasks that aren't already in the overdue list
        non_overdue_critical = [t for t in critical_tasks if t not in overdue_tasks]
        if non_overdue_critical:
            print(f"\n{Color.YELLOW}{Color.BOLD}  ⚠  HIGH PRIORITY TASKS ({len(non_overdue_critical)}):{Color.RESET}")
            for task in non_overdue_critical:
                print(
                    f"    {Color.YELLOW}▶ [{task.task_id:03d}] {task.title} "
                    f"— Score: {task.priority_score:.1f}/100 "
                    f"(Threshold: {CRITICAL_SCORE_THRESHOLD}){Color.RESET}"
                )

        self._print_separator("═", 80, Color.RED)
        print()

    # ── Main dashboard ────────────────────────────────────────────────────────

    def display_dashboard(self) -> None:
        """The main view — shows all active tasks sorted by priority score.

        Most urgent tasks are at the top. Each row shows the score,
        a visual bar, deadline status, importance, and complexity.
        """
        self._display_critical_alerts()

        active_tasks = self.manager.get_active_tasks(sort_by_score=True)

        # header
        print(f"\n{Color.BOLD}{Color.MAGENTA}{'Smart Task Prioritizer':^80}{Color.RESET}")
        print(
            f"{Color.DIM}"
            f"{'Dynamic Eisenhower Matrix — ' + datetime.now().strftime('%d/%m/%Y %H:%M'):^80}"
            f"{Color.RESET}"
        )
        self._print_separator()

        if not active_tasks:
            print(f"\n{Color.GREEN}  ✅ No active tasks. You're all caught up!{Color.RESET}\n")
            return

        # column headers
        header = (
            f"  {'#':>3}  "
            f"{'ID':>4}  "
            f"{'TITLE':<28}  "
            f"{'CATEGORY':<12}  "
            f"{'SCORE':>8}  "
            f"{'BAR':<17}  "
            f"{'DEADLINE':<22}  "
            f"{'IMP':>3}  "
            f"{'EST':>4}"
        )
        print(f"{Color.BOLD}{Color.WHITE}{header}{Color.RESET}")
        self._print_separator("─", 80)

        for rank, task in enumerate(active_tasks, start=1):
            score_color = self._score_color(task.priority_score)
            score_bar   = self._score_bar(task.priority_score)
            deadline_str = self._format_deadline(task.deadline)

            # colored dot based on urgency level
            dot = (
                f"{Color.RED}🔴"    if task.priority_score >= CRITICAL_SCORE_THRESHOLD else
                f"{Color.YELLOW}🟡" if task.priority_score >= 50 else
                f"{Color.CYAN}🔵"   if task.priority_score >= 25 else
                f"{Color.GREEN}🟢"
            )

            # trim long titles/categories so the table stays clean
            title_display = (task.title[:25] + "...") if len(task.title) > 28 else task.title
            cat_display   = (task.category[:10] + "..") if len(task.category) > 12 else task.category

            row = (
                f"  {dot} {rank:>2}  "
                f"[{task.task_id:03d}]  "
                f"{Color.BOLD}{title_display:<28}{Color.RESET}  "
                f"{Color.DIM}{cat_display:<12}{Color.RESET}  "
                f"{score_color}{task.priority_score:>7.1f}%{Color.RESET}  "
                f"{score_bar}  "
                f"{deadline_str:<22}  "
                f"{Color.MAGENTA}{task.importance:>3}{Color.RESET}  "
                f"{Color.CYAN}{task.complexity:>3}h{Color.RESET}"
            )
            print(row)

            # show the quadrant below each task row in a subtle style
            print(f"       {Color.DIM}└─ {task.quadrant}{Color.RESET}")

        self._print_separator()
        print(
            f"  {Color.DIM}Legend: IMP = Importance (1-10) | EST = Estimated hours | "
            f"Critical threshold: {CRITICAL_SCORE_THRESHOLD}%{Color.RESET}\n"
        )

    # ── Eisenhower matrix view ────────────────────────────────────────────────

    def display_eisenhower_matrix(self) -> None:
        """Shows tasks grouped by their Eisenhower quadrant.

        This is a great view when you want to decide what to focus on
        versus what to delegate or drop entirely.
        """
        quadrant_data = self.manager.get_tasks_by_quadrant()

        print(f"\n{Color.BOLD}{Color.MAGENTA}  ⚡ EISENHOWER MATRIX{Color.RESET}\n")
        self._print_separator("═")

        # each quadrant has its own color and action label
        quadrant_configs = [
            ("Q1 — Do it now (Critical)",    Color.RED,    "🔴 DO IT NOW"),
            ("Q2 — Schedule it (Important)", Color.BLUE,   "📅 SCHEDULE"),
            ("Q3 — Delegate it (Urgent)",    Color.YELLOW, "🤝 DELEGATE"),
            ("Q4 — Drop it (Low value)",     Color.DIM,    "🗑️  DROP IT"),
        ]

        for quadrant_key, color, label in quadrant_configs:
            tasks_in_q = quadrant_data.get(quadrant_key, [])
            print(f"\n{color}{Color.BOLD}  ┌─ {label} ({len(tasks_in_q)} task(s)){Color.RESET}")

            if not tasks_in_q:
                print(f"  {Color.DIM}│  (nothing here){Color.RESET}")
            else:
                for task in tasks_in_q:
                    days_left = _days_until_deadline(task.deadline)
                    time_info = (
                        f"{abs(days_left)}d overdue" if days_left < 0
                        else f"in {days_left}d"
                    )
                    print(
                        f"  {color}│  [{task.task_id:03d}] "
                        f"{Color.BOLD}{task.title}{Color.RESET}"
                        f"{color}  →  Score: {task.priority_score:.1f}%  |  "
                        f"{time_info}  |  Importance: {task.importance}/10{Color.RESET}"
                    )

            print(f"  {color}└{'─' * 60}{Color.RESET}")

        print()

    # ── Statistics view ───────────────────────────────────────────────────────

    def display_statistics(self) -> None:
        """Prints a simple overview of your task list health."""
        stats = self.manager.get_statistics()

        print(f"\n{Color.BOLD}{Color.MAGENTA}  📊 STATISTICS{Color.RESET}\n")
        self._print_separator("═")

        completion_bar = self._score_bar(stats["completion_rate"])

        rows = [
            ("Total tasks",        f"{stats['total']}",                           Color.WHITE),
            ("Active tasks",       f"{stats['active']}",                          Color.CYAN),
            ("Completed tasks",    f"{stats['completed']}",                        Color.GREEN),
            ("Critical tasks",     f"{stats['critical']}",                         Color.RED),
            ("Overdue tasks",      f"{stats['overdue']}",                          Color.RED),
            ("Average score",      f"{stats['avg_score']:.1f} / 100",              Color.YELLOW),
            ("Completion rate",    f"{completion_bar} {stats['completion_rate']}%", ""),
        ]

        for label, value, color in rows:
            print(f"  {Color.BOLD}{Color.WHITE}{label:<25}{Color.RESET}  {color}{value}{Color.RESET}")

        self._print_separator()

        # a simple project health label based on the average score
        # (low average score = most tasks are relaxed = good)
        health = 100 - stats["avg_score"]
        health_label = (
            f"{Color.GREEN}GREAT ✅"         if health > 60 else
            f"{Color.YELLOW}WATCH OUT ⚠️ "  if health > 30 else
            f"{Color.RED}CRITICAL 🚨"
        )
        print(f"\n  {Color.BOLD}Overall project health: {health_label}{Color.RESET}\n")

    # ── Input forms ───────────────────────────────────────────────────────────

    @staticmethod
    def _input_text(prompt: str, required: bool = True) -> str:
        """Prompts the user for text, re-asking if it's empty and required.

        Args:
            prompt: What to show the user.
            required: If True, won't accept an empty string.

        Returns:
            The cleaned text the user typed.
        """
        while True:
            value = input(f"  {Color.CYAN}{prompt}{Color.RESET}").strip()
            if value or not required:
                return value
            print(f"  {Color.RED}⚠ This field is required.{Color.RESET}")

    @staticmethod
    def _input_int(prompt: str, min_val: int, max_val: int) -> int:
        """Prompts for an integer and keeps asking until it's in the valid range.

        Args:
            prompt: What to show the user (without the range hint).
            min_val: Lowest acceptable value.
            max_val: Highest acceptable value.

        Returns:
            A validated integer.
        """
        while True:
            try:
                raw   = input(f"  {Color.CYAN}{prompt} [{min_val}-{max_val}]: {Color.RESET}").strip()
                value = int(raw)
                if min_val <= value <= max_val:
                    return value
                print(
                    f"  {Color.RED}⚠ Please enter a number between "
                    f"{min_val} and {max_val}.{Color.RESET}"
                )
            except ValueError:
                print(f"  {Color.RED}⚠ That doesn't look like a number. Try again.{Color.RESET}")

    @staticmethod
    def _input_date(prompt: str) -> str:
        """Prompts for a date and keeps asking until the format is correct.

        Args:
            prompt: What to show the user.

        Returns:
            A valid date string in YYYY-MM-DD format.
        """
        while True:
            raw = input(f"  {Color.CYAN}{prompt} (YYYY-MM-DD): {Color.RESET}").strip()
            try:
                datetime.strptime(raw, DATE_FORMAT)
                return raw
            except ValueError:
                print(
                    f"  {Color.RED}⚠ Invalid format. "
                    f"Use YYYY-MM-DD — for example: 2025-12-31.{Color.RESET}"
                )

    def _form_add_task(self) -> None:
        """Walks the user through adding a new task step by step."""
        print(f"\n{Color.BOLD}{Color.BLUE}  ➕ ADD A NEW TASK{Color.RESET}")
        self._print_separator()

        try:
            title       = self._input_text("Task title: ")
            description = self._input_text("Description (optional): ", required=False) or "N/A"
            deadline    = self._input_date("Deadline")
            importance  = self._input_int("Importance", 1, 10)
            complexity  = self._input_int("Estimated hours", 1, 100)
            category    = self._input_text("Category (e.g. Work, Personal): ", required=False) or "General"

            task = self.manager.add_task(
                title=title,
                description=description,
                deadline=deadline,
                importance=importance,
                complexity=complexity,
                category=category,
            )

            print(f"\n  {Color.GREEN}✅ Task '{task.title}' created!{Color.RESET}")
            print(
                f"     Priority score: "
                f"{self._score_color(task.priority_score)}"
                f"{task.priority_score:.1f}/100{Color.RESET}"
            )
            print(f"     Quadrant: {Color.BOLD}{task.quadrant}{Color.RESET}\n")

        except ValueError as e:
            print(f"\n  {Color.RED}❌ Validation error: {e}{Color.RESET}\n")

    def _form_complete_task(self) -> None:
        """Asks for a task ID and marks it as done."""
        print(f"\n{Color.BOLD}{Color.GREEN}  ✅ COMPLETE A TASK{Color.RESET}")
        self._print_separator()
        task_id = self._input_int("Task ID to complete", 1, 99999)
        if self.manager.complete_task(task_id):
            print(f"  {Color.GREEN}✅ Task ID {task_id} marked as complete!{Color.RESET}\n")
        else:
            print(f"  {Color.RED}❌ Task ID {task_id} not found.{Color.RESET}\n")

    def _form_delete_task(self) -> None:
        """Asks for a task ID and deletes it — with a confirmation step."""
        print(f"\n{Color.BOLD}{Color.RED}  🗑️  DELETE A TASK{Color.RESET}")
        self._print_separator()
        task_id = self._input_int("Task ID to delete", 1, 99999)

        task = self.manager.get_task_by_id(task_id)
        if not task:
            print(f"  {Color.RED}❌ Task ID {task_id} not found.{Color.RESET}\n")
            return

        # show what we found so the user knows what they're deleting
        print(
            f"  {Color.YELLOW}Found: '{task.title}' "
            f"(Score: {task.priority_score:.1f}){Color.RESET}"
        )
        confirm = input(
            f"  {Color.RED}Are you sure you want to delete this? (yes/no): {Color.RESET}"
        ).strip().lower()

        if confirm in ("yes", "y", "oui", "o"):
            self.manager.delete_task(task_id)
            print(f"  {Color.GREEN}✅ Task ID {task_id} deleted.{Color.RESET}\n")
        else:
            print(f"  {Color.DIM}Deletion cancelled.{Color.RESET}\n")

    # ── Main menu loop ────────────────────────────────────────────────────────

    def _display_menu(self) -> None:
        """Prints the main menu options."""
        print(f"\n{Color.BOLD}{Color.WHITE}  📋 MAIN MENU{Color.RESET}")
        self._print_separator("─", 40)
        for key, label in self.MENU_OPTIONS.items():
            icon = "🚪" if key == "0" else f" {key}."
            print(f"  {Color.CYAN}{icon}{Color.RESET}  {label}")
        self._print_separator("─", 40)

    def run(self) -> None:
        """Starts the app and keeps the menu loop running until the user quits.

        This is the main entry point for the UI. It refreshes all scores
        on startup so everything is up to date before the user sees anything.
        """
        # update scores first — deadlines may have changed since last run
        self.manager.refresh_all_scores()

        print(f"\n{Color.BOLD}{Color.MAGENTA}")
        print("  ╔══════════════════════════════════════════════════════╗")
        print("  ║          🧠  Smart Task Prioritizer  v2.0           ║")
        print("  ║        Intelligent Prioritization System             ║")
        print("  ╚══════════════════════════════════════════════════════╝")
        print(f"{Color.RESET}")

        while True:
            self._display_menu()
            choice = input(f"  {Color.BOLD}Your choice: {Color.RESET}").strip()

            if choice == "1":
                self.display_dashboard()
            elif choice == "2":
                self._form_add_task()
            elif choice == "3":
                self._form_complete_task()
            elif choice == "4":
                self._form_delete_task()
            elif choice == "5":
                self.display_eisenhower_matrix()
            elif choice == "6":
                self.display_statistics()
            elif choice == "7":
                self.manager.refresh_all_scores()
                print(f"  {Color.GREEN}✅ All scores refreshed!{Color.RESET}\n")
            elif choice == "0":
                print(f"\n  {Color.MAGENTA}{Color.BOLD}Goodbye! Stay productive. 🚀{Color.RESET}\n")
                sys.exit(0)
            else:
                print(f"  {Color.RED}⚠ Invalid option. Choose between 0 and 7.{Color.RESET}\n")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    """Boots up the app — sets up the manager and hands control to the CLI.

    Handles keyboard interrupts cleanly so Ctrl+C doesn't dump a traceback.
    """
    try:
        manager = TaskManager(tasks_file=TASKS_FILE)
        cli     = CLI(manager=manager)
        cli.run()
    except KeyboardInterrupt:
        print(f"\n\n  {Color.YELLOW}⚡ Interrupted. Closing cleanly...{Color.RESET}\n")
        sys.exit(0)
    except Exception as e:
        logger.critical("Unhandled fatal error: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
