from PIL import Image, ImageDraw
import hashlib

def get_left_coords(nb, debug=False):
    n = 50
    x = (nb % 3) * n
    y = (nb / 3) * n
    return [
        (x, y),
        (x, y + n),
        (x + n, y + n),
        (x + n, y),
    ]

def get_right_coords(nb):
    coords = get_left_coords(nb)
    for i in range(len(coords)):
        coords[i] = (300 - coords[i][0], coords[i][1])
    return coords

def generate_avatar(name):
    seed = hashlib.sha224(name.encode('utf-8')).digest()

    color = {
        'background': (250, 250, 250),
        'main': (seed[0], seed[1], seed[2]),
        }

    avatar = Image.new('RGB', (300, 300), color['background'])
    drav = ImageDraw.Draw(avatar)

    points = []
    for _ in range(3, 4 + seed[4] % 4):
        for i in range(5, 20):
            pt = seed[i] % 18
            if pt not in points:
                break
        points.append(pt)
        drav.polygon(get_left_coords(pt), fill=color['main'], outline=color['main'])
        drav.polygon(get_right_coords(pt), fill=color['main'], outline=color['main'])

    return avatar


if __name__ == "__main__":
    for name in ('plop', 'plip', 'plap'):
        avatar = generate_avatar(name)
        avatar.save(name + '.png', 'PNG')
