import math

grid = [
    [0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0],
    [0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0],
]


def heuristic(start, goal, strategy="manhattan"):
    return abs(start[0] - goal[0]) + abs(start[1] - goal[1])


def reconstruct_path(came_from, current):
    path = [current]

    while current in came_from.keys():
        path.append(came_from[current])
        current = came_from[current]

    return list(reversed(path))


# function RECONSTRUCT_PATH(came_from, current):
#     path = [current]
#     while current in came_from:
#         current = came_from[current]
#         insert current at start of path
#     return path


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

    return list(filter(lambda node: grid[node[0]][node[1]] == 0, neighbors))


def distance(a, b):
    return heuristic(a, b)


def a_star(start, goal):
    open_nodes = [start]  # priority queue ordered by min_f
    closed_nodes = []

    came_from = {}
    g_score = {}
    for r, row in enumerate(grid):
        for c, _ in enumerate(row):
            g_score[(r, c)] = math.inf
    g_score[start] = 0

    f_score = {}
    f_score[start] = heuristic(start, goal)

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
            tentative_g = g_score[current] + distance(current, neighbor)
            if tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score[neighbor] = tentative_g + heuristic(neighbor, goal)

                if neighbor not in open_nodes:
                    open_nodes.append(neighbor)
    return "failed"


print(a_star((0, 0), (4, 4)))

# function A_STAR(start, goal):


#         for each neighbor of current:
#             tentative_g = g_score[current] + distance(current, neighbor)

#             if tentative_g < g_score[neighbor]:   # found a better path
#                 came_from[neighbor] = current
#                 g_score[neighbor] = tentative_g
#                 f_score[neighbor] = tentative_g + heuristic(neighbor, goal)

#                 if neighbor not in open_set:
#                     add neighbor to open_set

#     return failure  # no path found


#     open_set = priority queue ordered by f = g + h
#     open_set.add(start)

#     came_from = empty map         # to reconstruct the path
#     g_score = map with default ∞  # cost from start to node
#     g_score[start] = 0

#     f_score = map with default ∞  # estimated total cost (start → node → goal)
#     f_score[start] = heuristic(start, goal)

#     while open_set is not empty:
#         current = node in open_set with lowest f_score

#         if current == goal:
#             return RECONSTRUCT_PATH(came_from, current)

#         remove current from open_set
