from picraft import World, Block, Vector, X, Y, Z, vector_range, line

world = World()
world.checkpoint.save()
world.events.track_players = world.players

p = world.player.tile_pos
GAME_AREA = vector_range(p - Vector(30, 2, 25), p + Vector(25, 20, 25) + 1)
DRAWING_AREA = vector_range(p - Vector(25, 1, 25), p + Vector(25, -1, 25) + 1)
WALKING_AREA = vector_range(DRAWING_AREA.start + Y, DRAWING_AREA.stop + Y)
CLEAR_BUTTON = p - Vector(30, 0, -23)
QUIT_BUTTON = p - Vector(30, 0, -25)

with world.connection.batch_start():
    world.blocks[GAME_AREA[:Vector(None, 2, None)]] = Block('dirt')
    world.blocks[GAME_AREA[Vector(None, 2, None):]] = Block('air')
    world.blocks[DRAWING_AREA] = Block('sand')
    world.blocks[QUIT_BUTTON] = Block('#ff0000')
    world.blocks[CLEAR_BUTTON] = Block('#ffff00')

def track_changes(old_state, new_state, default=Block('sand')):
    changes = {v: b for v, b in new_state.items() if old_state.get(v) != b}
    changes.update({v: default for v in old_state if v not in new_state})
    return changes

def draw_lines(old_state, lines):
    new_state = {
        v: Block('brick_block')
        for line_start, line_finish in lines
        for v in line(line_start, line_finish)
        }
    with world.connection.batch_start():
        for v, b in track_changes(old_state, new_state).items():
            world.blocks[v] = b
    return new_state

LINE_START = None
LINES = []
STATE = {}

@world.events.on_block_hit(pos=QUIT_BUTTON)
def quit_button(event):
    world.checkpoint.restore()
    world.connection.close()

@world.events.on_block_hit(pos=CLEAR_BUTTON)
def clear_button(event):
    global LINES, LINE_START, STATE
    LINES = []
    STATE = draw_lines(STATE, LINES)

@world.events.on_block_hit(pos=DRAWING_AREA, face='y+')
def toggle_draw(event):
    global LINE_START, STATE
    if LINE_START is None:
        LINE_START = event.pos
        LINES.append((LINE_START, LINE_START))
    elif LINE_START == event.pos:
        LINE_START = None
        del LINES[-1]
    else:
        LINES[-1] = (LINE_START, event.pos)
        LINE_START = event.pos
        LINES.append((LINE_START, LINE_START))
    STATE = draw_lines(STATE, LINES)

@world.events.on_player_pos(new_pos=WALKING_AREA)
def player_move(event):
    if LINE_START is not None:
        global STATE
        LINES[-1] = (LINE_START, event.new_pos.floor() - Y)
        STATE = draw_lines(STATE, LINES)

try:
    world.events.main_loop()
except:
    world.checkpoint.restore()
    raise
