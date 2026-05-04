# STgroupe1
## module complémentaire techniques de programmation
### mini project asked by prof Amiri
les membres du groupes:
1. Fateh Allah merazga
2. Boutaleb Abdelkader
3. Khouani Houssam Eddine
4. Khaddoum Maroua


# 🧠 Smart Task Prioritizer

<div align="center">
 **A command-line task manager that actually thinks.** 
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Dependencies](https://img.shields.io/badge/dependencies-none-brightgreen.svg)](#requirements)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#)
[![Status](https://img.shields.io/badge/status-stable-success.svg)](#)

*Instead of a flat to-do list, it scores every task dynamically based on deadline pressure, importance, and complexity — then maps it onto an Eisenhower Matrix so you always know what to work on next.*

</div>

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Preview](#-preview)
- [Features](#-features)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [How the Priority Score Works](#-how-the-priority-score-works)
- [Eisenhower Matrix](#-eisenhower-matrix)
- [Menu Options](#-menu-options)
- [Data Format](#-data-format)
- [Architecture](#-architecture)
- [Configuration](#-configuration)
- [Testing with Sample Data](#-testing-with-sample-data)
- [Contributing](#-contributing)
- [License](#-license)
- [Author](#-author)

---

## 🔍 Overview
 **Smart Task Prioritizer** is a zero-dependency Python CLI tool designed for developers, students, and professionals who need more than a static checklist. It treats prioritization as a **mathematical problem** , combining three weighted factors into a single actionable score, and visualizes the result using the proven Eisenhower decision framework.

---

## 📸 Preview

```
  ╔══════════════════════════════════════════════════════╗
  ║          🧠  Smart Task Prioritizer  v2.0            ║
  ║        Intelligent Prioritization System             ║
  ╚══════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════════════════════════
🚨  SYSTEM ALERT — CRITICAL TASKS DETECTED  🚨
════════════════════════════════════════════════════════════════════════════════
  📛 OVERDUE TASKS (1):
    ▶ [001] Annual report — 2 day(s) late (Score: 94.3/100)
════════════════════════════════════════════════════════════════════════════════

               Smart Task Prioritizer
      Dynamic Eisenhower Matrix — 15/07/2025 10:42
────────────────────────────────────────────────────────────────────────────────
  #    ID   TITLE                CATEGORY    SCORE    BAR            DEADLINE        IMP  EST
────────────────────────────────────────────────────────────────────────────────
🔴  1  [001] Annual report       Management   94.3%  ███████░░░░  ⚠ OVERDUE 2d     10   20h
         └─ Q1 — Do it now (Critical)
🔴  2  [008] Optimize SQL        Development  81.2%  ████████░░░  🔥 2d left        8    6h
         └─ Q1 — Do it now (Critical)
🟡  3  [002] PostgreSQL Migr...  Infra IT     67.4%  ██████░░░░░  ⏰ 5d left        9   40h
         └─ Q2 — Schedule it (Important)
```

---

## ✨ Features

| Feature | Description |
| :--- | :--- |
| 🎯 **Dynamic Priority Score** | Recalculated on every run using deadline, importance, and complexity |
| 📊 **Eisenhower Matrix** | Tasks automatically mapped to quadrants Q1 through Q4 |
| 🚨 **Critical Alerts** | Prominent red banner when tasks cross the danger threshold |
| 💾 **Safe File Storage** | Atomic writes to `tasks.json` prevent data corruption |
| ✅ **Full CRUD Support** | Add, complete, and delete tasks interactively |
| 📈 **Statistics View** | Completion rate, average score, and project health indicator |
| 🛡️ **Input Validation** | Every field is validated before being persisted |
| 🎨 **Color-Coded Output** | Red, yellow, cyan, and green urgency indicators |

---

## 🚀 Getting Started

### Requirements

- **Python 3.10** or higher
- **No external dependencies** — built entirely on the Python standard library

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/smart-task-prioritizer.git
cd smart-task-prioritizer

# 2. (Optional) Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # macOS / Linux
venv\Scripts\activate         # Windows

# 3. Launch the application
python main.py
```

> That's it. No `pip install`, no configuration files required.

### First Run

On the first launch, the application starts with an empty task list and creates `tasks.json` automatically the moment you add your first task.

Alternatively, drop the provided `tasks.json` sample file into the same folder as `main.py` to begin with **10 pre-loaded example tasks** .

---

## 📁 Project Structure

```
smart-task-prioritizer/
│
├── main.py          # The entire application (single clean file)
├── tasks.json       # Your task data (auto-created on first use)
└── README.md        # You are here
```

---

## 🧮 How the Priority Score Works

Every task is assigned a score from **0 to 100** . A higher value indicates greater urgency. The score is a weighted combination of three components:

$$
\text{Score} = (0.40 \times \text{Deadline}) + (0.35 \times \text{Importance}) + (0.25 \times \text{Complexity})
$$

### Component Breakdown

#### 1. Deadline Pressure — 40%

| Time Remaining | Behavior |
| :--- | :--- |
| Already overdue | Score = 100 (maximum) |
| Due today | Score = 100 (maximum) |
| 1 – 7 days left | Exponential spike — urgency jumps fast |
| 8 – 30 days left | Gentle linear decline |
| 30+ days left | Low baseline, barely above 0 |

An **exponential curve** is used for the final week so that the score doesn't just tick up linearly — it surges the way real urgency does.

#### 2. Importance — 35%

Simple linear normalization: the importance rating divided by 10, then multiplied by 100.

$$
\text{Importance Score} = \frac{\text{importance}}{10} \times 100
$$

> A task rated 8/10 scores **80 points** on this component.

#### 3. Complexity — 25%

A **logarithmic scale** is used so a 40-hour task isn't disproportionately boosted compared to a 20-hour one:

$$
\text{Complexity Score} = \frac{\log_2(\text{hours})}{\log_2(100)} \times 100
$$

### Alert Threshold

When a task's score reaches **75.0 or higher** , it triggers the red alert banner at the top of the dashboard. This threshold is configurable:

```python
CRITICAL_SCORE_THRESHOLD: float = 75.0  # line 20 of main.py
```

---

## 🗺️ Eisenhower Matrix

Every task is automatically placed in one of four quadrants:

```
                    URGENT              NOT URGENT
                ┌───────────────────┬───────────────────┐
  IMPORTANT     │  Q1               │  Q2               │
                │  Do it now        │  Schedule it      │
                │  🔴 Critical      │  📅 Plan          │
                ├───────────────────┼───────────────────┤
  NOT IMPORTANT │  Q3               │  Q4               │
                │  Delegate it      │  Drop it          │
                │  🤝 Urgent        │  🗑️  Low value    │
                └───────────────────┴───────────────────┘
```
 **Quadrant Assignment Rules:** 
- A task is **Urgent** if the deadline is **≤ 3 days** away **OR** its score exceeds the critical threshold.
- A task is **Important** if its importance rating is **≥ 7** .

---

## 📋 Menu Options

| Option | Action | Description |
| :---: | :--- | :--- |
| **1** | Show Dashboard | All active tasks sorted by score |
| **2** | Add a Task | Step-by-step task creation form |
| **3** | Complete a Task | Mark a task as done by ID |
| **4** | Delete a Task | Remove a task permanently (with confirmation) |
| **5** | Eisenhower Matrix View | Tasks grouped by quadrant |
| **6** | Statistics | Completion rate, averages, health score |
| **7** | Refresh Scores | Force-recalculate all priority scores |
| **0** | Quit | Exit the application |

---

## 🗂️ Data Format

Tasks are stored in a JSON array inside `tasks.json`. Each task follows this schema:

```json
{
    "task_id": 1,
    "title": "Submit annual report",
    "description": "Finalize and send the Q4 activity report.",
    "deadline": "2025-07-18",
    "importance": 10,
    "complexity": 20,
    "category": "Management",
    "completed": false,
    "created_at": "2025-07-01 09:00:00",
    "priority_score": 0.0,
    "quadrant": ""
}
```

> 💡 **Note:** `priority_score` and `quadrant` are recalculated fresh every time the app starts. You don't need to set them manually.

### Field Reference

| Field | Type | Required | Notes |
| :--- | :---: | :---: | :--- |
| `task_id` | int | ✅ | Must be unique |
| `title` | string | ✅ | Cannot be empty |
| `description` | string | ✅ | Use `"N/A"` if none |
| `deadline` | string | ✅ | Format: `YYYY-MM-DD` |
| `importance` | int | ✅ | Range: 1 to 10 |
| `complexity` | int | ✅ | Hours, range: 1 to 100 |
| `category` | string | ✅ | Free-text label |
| `completed` | bool | ✅ | `true` or `false` |
| `created_at` | string | ✅ | Set automatically |
| `priority_score` | float | — | Calculated on load |
| `quadrant` | string | — | Calculated on load |

---

## 🏗️ Architecture

```
main.py
│
├── Task  (dataclass)
│   ├── Stores all task fields
│   ├── Validates inputs on creation
│   ├── Calls calculate_priority_score() on load and create
│   └── Determines Eisenhower quadrant automatically
│
├── calculate_priority_score()   ← pure function, no side effects
│   ├── Deadline component   (40%) — exponential then linear curve
│   ├── Importance component (35%) — linear normalization
│   └── Complexity component (25%) — logarithmic normalization
│
├── TaskManager
│   ├── Loads tasks.json on startup
│   ├── Saves with atomic write (writes .tmp first, then swaps)
│   ├── CRUD: add, complete, delete, get_by_id
│   └── Queries: active, critical, overdue, by_quadrant, statistics
│
└── CLI
    ├── Reads from TaskManager, never touches files directly
    ├── Dashboard, Matrix, and Statistics views
    ├── Input forms with full validation
    └── Main menu loop (runs until the user presses 0)
```

### Design Principles

| Principle | Implementation |
| :--- | :--- |
| **Single Responsibility** | `Task` holds data, `TaskManager` handles logic, `CLI` handles display |
| **Fail-Safe Storage** | Atomic file writes prevent data loss on interruption |
| **Dynamic Scoring** | Scores are never stale — recalculated on every load |
| **Defensive Input** | Every user input is validated before touching any data |

---

## ⚙️ Configuration

All tweakable settings live at the top of `main.py`:

```python
TASKS_FILE = "tasks.json"         # storage file path
CRITICAL_SCORE_THRESHOLD = 75.0   # alert trigger threshold
DATE_FORMAT = "%Y-%m-%d"          # date format used everywhere
```

---

## 🧪 Testing with Sample Data

The provided `tasks.json` includes **10 real-world tasks** spanning multiple categories such as **IT, Business, Security, HR,** and **Development** . Some are overdue, some are due soon, and others are far away — all designed to showcase every quadrant and alert state from the very first run.

Ensure `tasks.json` is in the same folder as `main.py`, then:

```bash
python main.py
```

Then, from the menu:
- Press **1** to see the full dashboard
- Press **5** to see the Eisenhower Matrix
- Press **6** to see the statistics

---

## 🤝 Contributing

This project is intentionally kept as a single-file script for simplicity. If you'd like to extend it, here are some ideas:

- 🧪 Add **unit tests** in a `tests/` folder using `pytest`
- 📤 Add an `--export` flag to dump tasks as CSV or PDF reports
- 🖥️ Replace the CLI with a **Textual TUI** for a richer interface
- 🔁 Add **recurring tasks** with a frequency field
- 🔔 Integrate **desktop notifications** via `plyer` for critical alerts

Pull requests are welcome. Please keep code **PEP 8-compliant** and document any new features you introduce.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details. You are free to use, modify, and distribute it as you wish.

---

## 👤 Author

Built with **Python** and a lot of **coffee** ☕.
Feedback, bug reports, and feature requests are welcome via GitHub Issues.

---

<div align="center">

> *"What is important is seldom urgent, and what is urgent is seldom important."*
>
> — **Dwight D. Eisenhower** 
⭐ **END** ⭐

</div>
