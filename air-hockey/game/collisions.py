"""
collisions: puck-vs-paddle collision handling.
"""


def handle_paddle_collision(puck, paddle):
    """
    If the puck overlaps the paddle, bounce it off along the line joining
    the two centres (angle-based reflection), then push it clear of the
    paddle so they no longer overlap.

    Returns True if a collision was handled this frame.
    """
    dx = puck.x - paddle.x
    dy = puck.y - paddle.y
    distance = (dx ** 2 + dy ** 2) ** 0.5
    min_distance = puck.radius + paddle.radius

    if distance >= min_distance:
        return False

    # Contact normal: unit vector pointing from paddle centre to puck.
    # Fall back to a straight horizontal push if the centres coincide.
    if distance == 0:
        nx, ny = 1.0, 0.0
    else:
        nx, ny = dx / distance, dy / distance

    # Reflect the velocity about the contact normal:
    #   v' = v - 2 (v . n) n
    dot = puck.vx * nx + puck.vy * ny
    # Only reflect if the puck is actually moving into the paddle, so it
    # can't get flipped every frame and stick/vibrate inside.
    if dot < 0:
        puck.vx -= 2 * dot * nx
        puck.vy -= 2 * dot * ny

    # Separate: place the puck exactly on the paddle's surface so the two
    # no longer overlap (prevents tunnelling and getting stuck inside).
    puck.x = paddle.x + nx * min_distance
    puck.y = paddle.y + ny * min_distance

    return True
