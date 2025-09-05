import curses, time, random
from curses import wrapper

families = ["$", "#", ".", "%", "&"]

def most_frequent_ord(neis, idx_of, family_list):
    n_fams = len(family_list)
    counts = [0] * n_fams
    first_idx = [-1] * n_fams

    for i, fo in enumerate(neis):
        j = idx_of[fo]
        counts[j] += 1
        if first_idx[j] == -1:
            first_idx[j] = i

    maxc = -1
    bestj = 0
    for j, c in enumerate(counts):
        if c > maxc:
            maxc = c
            bestj = j
        elif c == maxc and c > 0 and first_idx[j] < first_idx[bestj]:
            bestj = j
    return family_list[bestj]


def main(stdscr_main):
    winner = False
    win_family = None
    generation = 0
    paused = False
    death_rate = 0
    family_dict = {family: 0 for family in families}

    stdscr_main.clear()
    curses.start_color()
    curses.use_default_colors()
    base_colors = [
        curses.COLOR_RED, curses.COLOR_BLUE, curses.COLOR_GREEN, curses.COLOR_YELLOW,
        curses.COLOR_MAGENTA, curses.COLOR_CYAN, curses.COLOR_WHITE
    ]
    color_pairs = {}
    for idx, fam in enumerate(families, start=1):
        fg = base_colors[(idx - 1) % len(base_colors)]
        curses.init_pair(idx, fg, -1)
        color_pairs[fam] = curses.color_pair(idx)

    sy, sx = stdscr_main.getmaxyx()

    width = (sx // 2) - 2
    begin_x = (sx // 2) // 2
    hud_height = 3
    hud_y = 0
    hud_win = stdscr_main.subwin(hud_height, width, hud_y, begin_x)

    begin_y = hud_height
    height = sy - begin_y - 1
    height = max(6, height)

    cell_screen = stdscr_main.subwin(height, width, begin_y, begin_x)
    cell_screen.box()

    addch = cell_screen.addch
    noutrefresh = cell_screen.noutrefresh
    SPACE_ORD = ord(' ')
    family_ords = {ord(f) for f in families}
    family_list = [ord(f) for f in families]
    idx_of = {fo: i for i, fo in enumerate(family_list)}
    family_ord_to_attr = {ord(f): color_pairs[f] for f in families}

    neighbor_offsets = (
        (-1,  0), ( 1,  0),
        ( 0, -1), ( 0,  1),
        (-1,  1), ( 1,  1),
        (-1, -1), ( 1, -1),
    )

    c_sy, c_sx = cell_screen.getmaxyx()
    y_start, y_end = 2, c_sy - 2
    x_start, x_end = 2, c_sx - 2

    grid = [bytearray([SPACE_ORD] * c_sx) for _ in range(c_sy)]

    def put(y, x, c_ord):
        grid[y][x] = c_ord
        if c_ord == SPACE_ORD:
            addch(y, x, ' ')
        else:
            addch(y, x, c_ord, family_ord_to_attr[c_ord])

    separation = ([width // (len(families) + 1) + (1 if x < width % len(families) else 0) for x in range(len(families))])
    for i, (family, sep) in enumerate(zip(families, separation)):
        fam_ord = ord(family)
        x0 = max(1, (sep * (i + 1)) - 10)
        x1 = min(width - 2, (sep * (i + 1)))
        y0 = max(1, (((sy + len(families)) // 2) - 5) - begin_y)
        y1 = min(height - 2, ((sy // 2) + 5) - begin_y)

        for x in range(x0, x1):
            for y in range(y0, y1):
                if random.randint(0, 10) >= 5:
                    put(y, x, fam_ord)

    stdscr_main.nodelay(True)

    def draw_hud():
        hud_win.erase()

        state = "WIN" if win_family else ("PAUSED" if paused else "RUN")
        header = f"Gen:{generation}  State:{state}  Deaths:{death_rate}"
        if win_family:
            header += f"  Winner:{win_family}"
        x_center = max(0, (width - len(header)) // 2)
        try:
            hud_win.addstr(0, x_center, header)
        except curses.error:
            pass

        total = sum(family_dict.values())
        inner_w = max(10, width - 2)
        x = 1
        if total > 0:
            remaining = inner_w
            for idx, fam in enumerate(families):
                count = family_dict.get(fam, 0)
                seg_len = remaining if idx == len(families) - 1 else int(round((count / total) * inner_w))
                seg_len = max(0, min(seg_len, remaining))
                for i in range(seg_len):
                    try:
                        hud_win.addch(1, x + i, ord('█'), color_pairs[fam])
                    except curses.error:
                        pass
                x += seg_len
                remaining = max(0, inner_w - (x - 1))
        else:
            for i in range(inner_w):
                try:
                    hud_win.addch(1, 1 + i, ord('-'))
                except curses.error:
                    pass

        col_x = 1
        for fam in families:
            count = family_dict.get(fam, 0)
            pct = (count * 100 // total) if total > 0 else 0
            seg = f" {fam}:{pct}% "
            try:
                hud_win.addstr(2, col_x, seg, color_pairs[fam])
            except curses.error:
                pass
            col_x += len(seg)

        hud_win.noutrefresh()

    def render_win_effect(winner_fam):
        try:
            fam_attr = color_pairs[winner_fam] | curses.A_BOLD
        except KeyError:
            fam_attr = curses.A_BOLD

        msg = f"{winner_fam} WINS!  Generation {generation}"
        banner_w = min(width - 4, len(msg) + 10)
        bx = max(2, (width - banner_w) // 2)
        by = c_sy // 2

        for k in range(10):
            pulse_attr = fam_attr | (curses.A_REVERSE if k % 2 == 0 else 0)

            for x in range(c_sx):
                try:
                    cell_screen.addch(0, x, ord(' '), pulse_attr)
                    cell_screen.addch(c_sy - 1, x, ord(' '), pulse_attr)
                except curses.error:
                    pass
            for y in range(c_sy):
                try:
                    cell_screen.addch(y, 0, ord(' '), pulse_attr)
                    cell_screen.addch(y, c_sx - 1, ord(' '), pulse_attr)
                except curses.error:
                    pass

            for i in range(banner_w):
                try:
                    cell_screen.addch(by, bx + i, ord(' '), pulse_attr)
                except curses.error:
                    pass
            try:
                cell_screen.addstr(by, bx + (banner_w - len(msg)) // 2, msg, pulse_attr)
            except curses.error:
                pass

            draw_hud()
            noutrefresh()
            hud_win.noutrefresh()
            stdscr_main.noutrefresh()
            curses.doupdate()
            time.sleep(0.12)

        for i in range(banner_w):
            try:
                cell_screen.addch(by, bx + i, ord(' '), fam_attr)
            except curses.error:
                pass
        try:
            cell_screen.addstr(by, bx + (banner_w - len(msg)) // 2, msg, fam_attr)
        except curses.error:
            pass
        noutrefresh()
        hud_win.noutrefresh()
        stdscr_main.noutrefresh()
        curses.doupdate()

    while not winner:
        c = stdscr_main.getch()
        if c == ord(' '):
            paused = not paused

        if not paused:
            family_dict = {family: 0 for family in families}
            death_rate = 0

            for x in range(x_start, x_end):
                for y in range(y_start, y_end):
                    cell_val = grid[y][x]
                    is_alive = (cell_val in family_ords)

                    cnt = 0
                    surrounding = None

                    for dy, dx in neighbor_offsets:
                        n = grid[y + dy][x + dx]
                        if n in family_ords:
                            cnt += 1
                            if surrounding is None and cnt == 1 and not is_alive:
                                surrounding = [n]
                            elif surrounding is not None:
                                surrounding.append(n)
                            if cnt > 3:
                                break

                    if is_alive:
                        if cnt < 2 or cnt > 3:
                            if cell_val != SPACE_ORD:
                                put(y, x, SPACE_ORD)
                                death_rate += 1
                        else:
                            family_dict[chr(cell_val)] += 1
                    else:
                        if cnt == 3:
                            if surrounding is None:
                                surrounding = []
                                for dy, dx in neighbor_offsets:
                                    n = grid[y + dy][x + dx]
                                    if n in family_ords:
                                        surrounding.append(n)
                            new_family = most_frequent_ord(surrounding, idx_of, family_list)
                            put(y, x, new_family)
                            family_dict[chr(new_family)] += 1

            generation += 1

            alive_total = sum(family_dict.values())
            if alive_total > 0:
                active = [fam for fam in families if family_dict.get(fam, 0) > 0]
                if len(active) == 1:
                    win_family = active[0]
                    paused = True
                    draw_hud()
                    noutrefresh()
                    stdscr_main.noutrefresh()
                    curses.doupdate()
                    render_win_effect(win_family)
                    winner = True

        draw_hud()
        noutrefresh()
        stdscr_main.noutrefresh()
        curses.doupdate()

    stdscr_main.nodelay(False)
    stdscr_main.refresh()
    cell_screen.refresh()
    stdscr_main.getch()

wrapper(main)
