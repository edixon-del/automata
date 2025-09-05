import curses, time, random
from curses import wrapper

families = ["$", "."]

def most_frequent(c_list):
    if not c_list:
        raise IndexError("List is empty")

    counter = 0
    num = c_list[0]

    for k in c_list:
        curr_frequency = c_list.count(k)
        if curr_frequency > counter:
            counter = curr_frequency
            num = k

    return num

def check(cell_screen, yc, x, family_dict, neighbors, surrounding):
    direction = chr(cell_screen.inch(yc, x) & 0xFF)
    if direction in families:
        neighbors[0] += 1
        surrounding.append(direction)
        for p in range(len(families)):
            if direction == families[p]:
                family_dict["{}".format(families[p])] += 1

def main(stdscr_main):
    winner = False
    generation = 0
    paused = False
    death_rate = 0
    family_dict = {family: 0 for family in families}
    stdscr_main.clear()
    curses.start_color()
    curses.use_default_colors()
    color_pairs = {}
    curses.init_pair(1, curses.COLOR_RED, -1)
    curses.init_pair(2, curses.COLOR_CYAN, -1)
    color_pairs[families[0]] = curses.color_pair(1)
    color_pairs[families[1]] = curses.color_pair(2)
    sy, sx = stdscr_main.getmaxyx()
    width = (sx // 2) - 2
    height = sy - 4
    begin_y = 2
    begin_x = (sx//2)//2
    cell_screen = stdscr_main.subwin(height, width, begin_y, begin_x)
    cell_screen.box()
    separation = ([width // (len(families) + 1) + (1 if x < width % len(families) else 0) for x in range(len(families))])
    for i, (family, sep) in enumerate(zip(families, separation)):
        for x in range((sep * (i + 1)) - 10, (sep * (i + 1))):
            for y in range((((sy + len(families)) // 2) - 5), ((sy // 2) + 5)):
                chance = random.randint(0, 10)
                if chance >= 5:
                    cell_screen.addstr(y, x, family, color_pairs[family])
    stdscr_main.nodelay(True)
    while True and winner is False:
        c = stdscr_main.getch()
        if c == ord(' '):
            paused = not paused
        if not paused:
            sy, sx = cell_screen.getmaxyx()
            for x in range(2, (sx - 2)):
                for y in range(2, (sy - 2)):
                    cell_val = cell_screen.inch(y, x) & 0xFF
                    current_character = chr(cell_val)
                    neighbors = [0]
                    surrounding = []
                    check(cell_screen, y - 1, x, family_dict, neighbors, surrounding)  # above
                    check(cell_screen, y + 1, x, family_dict, neighbors, surrounding)  # below
                    check(cell_screen, y, x - 1, family_dict, neighbors, surrounding)  # left
                    check(cell_screen, y, x + 1, family_dict, neighbors, surrounding)  # right
                    check(cell_screen, y - 1, x + 1, family_dict, neighbors, surrounding)  # top right
                    check(cell_screen, y + 1, x + 1, family_dict, neighbors, surrounding)  # bottom right
                    check(cell_screen, y - 1, x - 1, family_dict, neighbors, surrounding)  # top left
                    check(cell_screen, y + 1, x - 1, family_dict, neighbors, surrounding)  # bottom left
                    if current_character in families:
                        for i in range(len(families)):
                            if current_character == families[i]:
                                family_dict["{0}".format(families[i])] += 1
                        if neighbors[0] < 2:
                            cell_screen.addstr(y, x, ' ')
                            death_rate += 1
                        if neighbors[0] > 3:
                            cell_screen.addstr(y, x, ' ')
                            death_rate += 1
                    elif current_character == ' ':
                        if neighbors[0] == 3:
                            new_family = most_frequent(surrounding)
                            cell_screen.addstr(y, x, new_family, color_pairs[new_family])
                            current_char = chr(cell_screen.inch(y, x) & 0xFF)
                            for i in range(len(families)):
                                if current_char == families[i]:
                                    family_dict["{0}".format(families[i])] += 1
            generation += 1
            stdscr_main.refresh()
            cell_screen.refresh()
    stdscr_main.nodelay(False)
    stdscr_main.refresh()
    cell_screen.refresh()
    stdscr_main.getch()

wrapper(main)