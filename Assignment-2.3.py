import turtle
import math

# Recursive function to draw a fractal edge
def fractal_side(size, level):
    if level == 0:
        turtle.forward(size)
    else:
        step = size / 3
        fractal_side(step, level - 1)
        turtle.left(60)        # inward spike
        fractal_side(step, level - 1)
        turtle.right(120)
        fractal_side(step, level - 1)
        turtle.left(60)
        fractal_side(step, level - 1)

# Function to draw the full shape
def draw_shape(n_sides, side_len, level):
    turn = 360 / n_sides
    for _ in range(n_sides):
        fractal_side(side_len, level)
        turtle.left(turn)

def main():
    n = int(input("Number of polygon sides: "))
    s = int(input("Length of each side: "))
    d = int(input("Recursion depth: "))

    turtle.speed("fastest")
    turtle.hideturtle()

    # --- Positioning so shape is centered ---
    approx_radius = s / (2 * math.sin(math.pi / n))
    turtle.penup()
    turtle.setpos(-s/2, -approx_radius/3)   # shift starting point
    turtle.pendown()

    draw_shape(n, s, d)

    turtle.done()

if __name__ == "__main__":
    main()
