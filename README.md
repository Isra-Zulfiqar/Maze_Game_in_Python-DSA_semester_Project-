Neon Maze: Pathfinder's Journey
An interactive maze game that visualizes classic pathfinding algorithms in real‑time using Python & Pygame.



 Overview

Neon Maze is an educational game that demonstrates **Data Structures and Algorithms** through gameplay.  
You control a glowing character through a procedurally generated maze, collect coins, avoid enemies, and reach the exit – all while watching **BFS, Dijkstra, and A*** find their paths in real time.

---

Features

- 🧱 **Random Maze Generation** – Recursive Backtracking (stack‑based DFS), guaranteed solvable.
- 🧠 **3 Pathfinding Algorithms** visualized simultaneously (toggle with `F` key):
  - **BFS** (blue) – shortest path in steps, uses a queue.
  - **Dijkstra** (red) – lowest‑cost path (uniform weight = 1), uses a priority queue.
  - **A*** (green) – heuristic‑guided search, uses priority queue + Manhattan distance.
- 🕹️ **Smooth Player Movement** – grid‑based with interpolation, move queueing, and a glowing trail.
- 👾 **Enemy AI** – random movement that reacts to walls.
- 🪙 **Coin Collection** – 15 coins per level, score + particle effects.
- 🚪 **Level Progression** – reach the exit, get bonus points (time + moves), advance to next level.
- 🎨 **Neon Visuals** – particle system, pulsing glows, animated UI, custom cursor.
- 🧭 **Responsive UI** – resizable window, state‑based menus (menu, playing, paused, game over, win).
- ⌨️ **Keyboard & Mouse Controls** – full support for both.

---

## 🛠️ Technologies

- **Language**: Python 3.x
- **Library**: Pygame (graphics, input, timing)
- **Data Structures**:
  - `list` – grid storage, particle pools, button lists
  - `deque` – BFS queue
  - `heapq` – priority queue for Dijkstra / A*
  - `set` – visited nodes tracking
  - `dict` – distances, predecessors, g‑scores
  - `Enum` – direction constants
- **Algorithms**:
  - Recursive Backtracking (maze generation)
  - BFS, Dijkstra, A* (pathfinding)

---

## 🎮 How to Play

1. **Start** – Click "Start Game" from the main menu.
2. **Move** – Use **WASD** or **Arrow Keys**.
3. **Collect Coins** – Each gold coin gives +10 points.
4. **Avoid Enemies** – Red circles that wander randomly. Touching one ends the game.
5. **Reach the Exit** – The green pulsing circle at the bottom‑right.
6. **Toggle Pathfinding** – Press `F` to see BFS (blue), Dijkstra (red) and A* (green) paths.
7. **Pause** – Press `P` or `ESC`.
8. **Restart** – Press `R` (while playing) or use the button.

---

## 📥 Installation & Running

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/neon-maze.git
cd neon-maze

pip install pygame
