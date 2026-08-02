# visual_grid_game.py
import random
import tkinter as tk


class VisualGridHuntGame:
    """A flexible Pacman-style grid environment with support for configurable opponents and larger scales."""

    def __init__(self, width=10, height=10, num_food=10, num_opponents=2, custom_walls=None, num_traps=8):
        self.width = width
        self.height = height
        self.agent_pos = [0, 0]  # Starting position (x, y)

        if custom_walls is not None:
            self.walls = set(custom_walls)
        else:
            # Generate some default scattered walls for a larger grid
            self.walls = {(3, 5), (4, 5), (2, 5), (2, 6), (2, 7), (4,6), (4,7)}

        # Dynamically generate random food positions avoiding walls and agent start
        self.food_positions = set()
        while len(self.food_positions) < num_food:
            fx = random.randint(0, self.width - 1)
            fy = random.randint(0, self.height - 1)
            pos_tuple = (fx, fy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls:
                self.food_positions.add(pos_tuple)

        # Declaring new trap collection
        self.toxic_traps = set()
        while len(self.toxic_traps) < num_traps:
            gx = random.randint(0, self.width - 1)
            gy = random.randint(0, self.height - 1)
            pos_tuple = (gx, gy)
            if pos_tuple != (0, 0) and pos_tuple not in self.walls and pos_tuple not in self.food_positions:
                self.toxic_traps.add(pos_tuple)

        # Generate adversarial opponents
        self.opponents = []
        while len(self.opponents) < num_opponents:
            ox = random.randint(0, self.width - 1)
            oy = random.randint(0, self.height - 1)
            op_pos = [ox, oy]
            if tuple(op_pos) != (0, 0) and tuple(op_pos) not in self.walls and tuple(op_pos) not in self.food_positions:
                self.opponents.append(op_pos)

        self.score = 0
        self.steps = 0
        self.collision = False

    def get_percept(self) -> dict:
        ax,ay = self.agent_pos

        current_facing = getattr(self, 'facing', 'Up')

        if current_facing == 'Up':
            target_cell = (ax, ay + 1)
        elif current_facing == 'Down':
            target_cell = (ax, ay - 1)
        elif current_facing == 'Left':
            target_cell = (ax - 1, ay)
        elif current_facing == 'Right':
            target_cell = (ax + 1, ay)

        wall_ahead = False
        if (target_cell[0] < 0 or target_cell[0] >= self.width or
            target_cell[1] < 0 or target_cell[1] >= self.height or
            target_cell in getattr(self, 'walls', [])):
            wall_ahead = True
       
        food_here = tuple(self.agent_pos) in self.food_positions

        trap_ahead = target_cell in self.toxic_traps
        smells_toxin = tuple(self.agent_pos) in self.toxic_traps

        safe_actions = []
        for act, (dx, dy) in [('Up', (0, 1)), ('Down', (0, -1)), ('Left', (-1, 0)), ('Right', (1, 0))]:
            nx, ny = ax + dx, ay + dy
            if (0 <= nx < self.width and 0 <= ny < self.height and
                (nx, ny) not in self.walls and (nx, ny) not in self.toxic_traps):
                safe_actions.append(act)

        return {
            'wall_ahead': wall_ahead,
            'food_here': food_here,
            'trap_ahead': trap_ahead,
            'smells_toxin': smells_toxin,
            'safe_actions': safe_actions,
            'agent_pos': list(self.agent_pos),
            'food_positions': list(self.food_positions)
        }

        ''' return {
            'agent_pos': list(self.agent_pos),
            'opponent_positions': [list(op) for op in self.opponents],
            'smells_food': tuple(self.agent_pos) in self.food_positions,
            'hit_wall': tuple(self.agent_pos) in self.walls,
            'collision': self.collision,
            'score': self.score,
            'remaining_food': len(self.food_positions),
            'smells_toxin': tuple(self.agent_pos) in self.toxic_traps
        } '''

    def execute_action(self, action: str):
        self.steps += 1
        new_pos = list(self.agent_pos)

        if action == 'Up':
            new_pos[1] = min(self.height - 1, new_pos[1] + 1)
        elif action == 'Down':
            new_pos[1] = max(0, new_pos[1] - 1)
        elif action == 'Left':
            new_pos[0] = max(0, new_pos[0] - 1)
        elif action == 'Right':
            new_pos[0] = min(self.width - 1, new_pos[0] + 1)

        if tuple(new_pos) in self.walls:
            self.score -= 5
        else:
            if tuple(new_pos) in self.toxic_traps:
                self.score -= 15
            self.agent_pos = new_pos

        tuple_pos = tuple(self.agent_pos)
        if tuple_pos in self.food_positions:
            self.food_positions.remove(tuple_pos)
            self.score += 20

        for op in self.opponents:
            move = random.choice(['Up', 'Down', 'Left', 'Right', 'Stay'])
            if move == 'Up' and op[1] < self.height - 1:
                op[1] += 1
            elif move == 'Down' and op[1] > 0:
                op[1] -= 1
            elif move == 'Left' and op[0] > 0:
                op[0] -= 1
            elif move == 'Right' and op[0] < self.width - 1:
                op[0] += 1

            if op == self.agent_pos:
                self.score -= 50
                self.collision = True

    def is_done(self) -> bool:
        return len(self.food_positions) == 0 or self.steps >= 60 or self.collision


class GridGameGUI:
    """Tkinter wrapper that dynamically scales cell sizes to keep larger grids on screen."""

    def __init__(self, root, width=100, height=100, num_food=12, num_opponents=2, walls=None, agent=None):
        self.root = root
        self.root.title("IT3012 - Scalable Multi-Agent Grid Hunt")

        self.env = VisualGridHuntGame(width=width, height=height, num_food=num_food, num_opponents=num_opponents,
                                      custom_walls=walls)
        self.agent = agent if agent is not None else SimpleReflexAgent()

        # Dynamically calculate cell size so the total canvas fits nicely within a 600x600 window ceiling
        max_canvas_dim = 600
       
        self.cell_size = max(20, min(max_canvas_dim // self.env.width, max_canvas_dim // self.env.height))

        canvas_w = self.env.width * self.cell_size
        canvas_h = self.env.height * self.cell_size

        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack()

        self.label = tk.Label(root, text="Score: 0 | Steps: 0", font=("Arial", 14))
        self.label.pack(pady=10)

        self.btn = tk.Button(root, text="Start Simulation", command=self.run_loop, font=("Arial", 12), bg="#000066",
                             fg="white")
        self.btn.pack(pady=5)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete("all")

        for x in range(self.env.width):
            for y in range(self.env.height):
                x1 = x * self.cell_size
                y1 = (self.env.height - 1 - y) * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size

                color = "#2D3333" if (x, y) not in self.env.walls else "#64748b"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="#cbd5e1")

                # Only draw text if cell is large enough
                if self.cell_size >= 40 and (x, y) in self.env.walls:
                    self.canvas.create_text(x1 + self.cell_size / 2, y1 + self.cell_size / 2, text="W", fill="white",
                                            font=("Arial", 8, "bold"))

        for fx, fy in self.env.food_positions:
            offset = self.cell_size * 0.25
            x1 = fx * self.cell_size + offset
            y1 = (self.env.height - 1 - fy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#f59e0b",
                                    outline="#d97706")

        for gx, gy in self.env.toxic_traps:
            offset = self.cell_size * 0.3
            x1 = gx * self.cell_size + offset
            y1 = (self.env.height - 1 - gy) * self.cell_size + offset
            self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.5, y1 + self.cell_size * 0.5, fill="#800080",
                                    outline="#cea2fd")

        for ox, oy in self.env.opponents:
            offset = self.cell_size * 0.2
            x1 = ox * self.cell_size + offset
            y1 = (self.env.height - 1 - oy) * self.cell_size + offset
            self.canvas.create_rectangle(x1, y1, x1 + self.cell_size * 0.6, y1 + self.cell_size * 0.6, fill="#990000",
                                         outline="#7a0000")

        ax, ay = self.env.agent_pos
        offset = self.cell_size * 0.15
        x1 = ax * self.cell_size + offset
        y1 = (self.env.height - 1 - ay) * self.cell_size + offset
        self.canvas.create_oval(x1, y1, x1 + self.cell_size * 0.7, y1 + self.cell_size * 0.7, fill="#000066",
                                outline="#1e3a8a")

    def run_loop(self):
        self.btn.config(state="disabled")

        def step():
            if not self.env.is_done():
                percept = self.env.get_percept()
                action = self.agent.sense_and_act(percept)
                if not action or action not in ['Up', 'Down', 'Left', 'Right']:
                    action = random.choice(['Up', 'Down', 'Left', 'Right'])
                self.env.execute_action(action)

                self.draw_grid()
                self.label.config(text=f"Score: {self.env.score} | Steps: {self.env.steps} | Action: {action}")
                self.root.after(250, step)
            else:
                end_text = f"Collision! Game Over! Final Score: {self.env.score}" if self.env.collision else f"Finished! Final Score: {self.env.score}"
                self.label.config(text=end_text)
                self.btn.config(state="normal")

        step()


class SimpleReflexAgent:

    def sense_and_act(self, percept: dict) -> str:
        safe_actions = percept.get('safe_actions', [])
        wall_ahead = percept.get('wall_ahead', False)
        trap_ahead = percept.get('trap_ahead', False)

        # Filter actions that are safe from walls and traps
        possible_actions = safe_actions if safe_actions else ['Up', 'Down', 'Left', 'Right']
        if wall_ahead or trap_ahead:
            possible_actions = [a for a in possible_actions if a != 'Up']

        if not possible_actions:
            possible_actions = ['Left', 'Down', 'Right']

        food_positions = percept.get('food_positions', [])
        agent_pos = percept.get('agent_pos', None)

        if food_positions and agent_pos:
            ax, ay = agent_pos
            best_action = possible_actions[0]
            min_dist = float('inf')
            for act in possible_actions:
                nx, ny = ax, ay
                if act == 'Up': ny += 1
                elif act == 'Down': ny -= 1
                elif act == 'Left': nx -= 1
                elif act == 'Right': nx += 1

                dist = min(abs(nx - fx) + abs(ny - fy) for fx, fy in food_positions)
                if dist < min_dist:
                    min_dist = dist
                    best_action = act
            return best_action

        return random.choice(possible_actions)

class ModelBasedAgent:
   
    def __init__(self):

        self.visited_cells = set()

        self.rel_x = 0
        self.rel_y = 0

        self.last_action = None

        def _update_internal_state(self):

            if self.last_action == 'Up':
                self.rel_y += 1
            elif self.last_action == 'Down':
                self.rel_y -= 1
            elif self.last_action == 'Left':
                self.rel_x -= 1
            elif self.last_action == 'Right':
                self.rel_y += 1

            self.visited_cells.add((self.rel_x, self.rel_y))

        def sense_and_act(self, percept: dict):

            self._update_internal_state()

            wall_ahead = percept.get_percept('wall_ahead', False)

            left_cell = (self.rel_x - 1, self.rel_y)
            left_is_visited = left_cell in self.visited_cells

            if wall_ahead or left_is_visited:
                action = 'Right'
            elif wall_ahead:
                action = 'Left'
            elif self.visited_cells:
                action = 'Down'  
            else:
                action = 'Up'

            self.last_action = action

            return action


if __name__ == "__main__":
    root = tk.Tk()
    # Try a larger grid size like 12x12 with 15 food and 3 opponents!
    app = GridGameGUI(root, width=12, height=12, num_food=15, num_opponents=0)
    root.mainloop()