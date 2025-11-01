import math


def heuristic(start, goal, strategy):
    match strategy:
        case "manhattan":
            return abs(start[0] - goal[0]) + abs(start[1] - goal[1])
        case "euclidian":
            return math.sqrt((start[0] - goal[0]) ** 2 + (start[1] - goal[1]) ** 2)
    return 0


def reconstruct_path(came_from, current):
    path = [current]

    while current in came_from.keys():
        path.append(came_from[current])
        current = came_from[current]

    return list(reversed(path))


def get_neighbors(node, grid):
    neighbors = []
    is_at_left_edge = node[0] == 0
    is_at_right_edge = node[0] == len(grid[0]) - 1
    is_at_top_edge = node[1] == 0
    is_at_bottom_edge = node[1] == len(grid) - 1

    if not is_at_left_edge:  # east
        neighbors.append((node[0] - 1, node[1]))
        if not is_at_top_edge:  # northeast
            neighbors.append((node[0] - 1, node[1] - 1))
        if not is_at_bottom_edge:  # southeast
            neighbors.append((node[0] - 1, node[1] + 1))
    if not is_at_right_edge:  # west
        neighbors.append((node[0] + 1, node[1]))
        if not is_at_top_edge:  # northwest
            neighbors.append((node[0] + 1, node[1] - 1))
        if not is_at_bottom_edge:  # southwest
            neighbors.append((node[0] + 1, node[1] + 1))
    if not is_at_top_edge:  # north
        neighbors.append((node[0], node[1] - 1))
    if not is_at_bottom_edge:  # south
        neighbors.append((node[0], node[1] + 1))
    return list(filter(lambda node: grid[node[1]][node[0]] == 0, neighbors))


def distance(a, b, strategy):
    return heuristic(a, b, strategy)


def a_star(start, goal, grid, strategy="manhattan"):
    open_nodes = [start]  # priority queue ordered by min_f
    closed_nodes = []

    came_from = {}
    g_score = {}
    for r, row in enumerate(grid):
        for c, _ in enumerate(row):
            g_score[(c, r)] = math.inf
    g_score[start] = 0

    f_score = {}
    f_score[start] = heuristic(start, goal, strategy)

    while len(open_nodes) != 0:
        current = open_nodes[0]
        if current == goal:
            return reconstruct_path(came_from, current)

        open_nodes.remove(current)
        closed_nodes.append(current)

        neighbors = get_neighbors(current, grid)

        for neighbor in neighbors:
            if neighbor in closed_nodes:
                continue
            tentative_g = g_score[current] + distance(current, neighbor, strategy)
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal, strategy)

                if neighbor not in open_nodes:
                    open_nodes.append(neighbor)
    return False
