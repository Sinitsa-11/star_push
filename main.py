import random
import sys
import copy
import os
import pygame
from pygame.locals import *

pygame.init()
pygame.mixer.music.load('igra_prestolov_-_glavnaja_tema_iz_igra_prestolov_(z3.fm).mp3')
pygame.mixer.music.play(-1)
sound_wall = pygame.mixer.Sound('hi-tech-delete-button-interace.mp3')
char_sound = pygame.mixer.Sound('2e4654648a969a5.mp3')
star_sound = pygame.mixer.Sound('531c6a581110c5a.mp3')


def run_level(level, level_num):
    global current_image
    level_object = level[level_num]
    map_object = decorate_map(level_object['map_object'], level_object['startState']['player'])
    game_object = copy.deepcopy(level_object['startState'])
    map_needs_redraw = True  # вызываем draw_мap()
    level_surf = basic_font.render('Level %s of %s' % (level_num + 1, len(level)), 1, text_color)
    level_rect = level_surf.get_rect()
    level_rect.bottomleft = (20, HEIGHT - 35)
    map_width = len(map_object) * tile_width
    map_height = (len(map_object[0]) - 1) * tile_floor_height + tile_height
    max_cam_x_pan = abs(HALF_HEIGHT - int(map_height / 2)) + tile_width
    max_cam_y_pan = abs(HALF_WIDTH - int(map_width / 2)) + tile_height

    level_is_complete = False
    # перемещение камеры
    camera_offset_x = 0
    camera_offset_y = 0
    # проверка нажаты ли клавиши перемещения камеры
    camera_up = False
    camera_down = False
    camera_left = False
    camera_right = False

    while True:
        player_move_to = None
        key_pressed = False

        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            # настройка перемещений персонажа
            elif event.type == KEYDOWN:
                key_pressed = True
                if event.key == K_LEFT:
                    player_move_to = LEFT
                elif event.key == K_RIGHT:
                    player_move_to = RIGHT
                elif event.key == K_UP:
                    player_move_to = UP
                elif event.key == K_DOWN:
                    player_move_to = DOWN
                # настройка камеры
                elif event.key == K_a:
                    camera_left = True
                elif event.key == K_d:
                    camera_right = True
                elif event.key == K_w:
                    camera_up = True
                elif event.key == K_s:
                    camera_down = True

                elif event.key == K_n:
                    return 'next'
                elif event.key == K_b:
                    return 'back'

                elif event.key == K_ESCAPE:
                    terminate()
                elif event.key == K_BACKSPACE:
                    return 'reset'
                elif event.key == K_p:
                    # смена персонажа на следующего
                    current_image += 1
                    if current_image >= len(player_images):
                        current_image = 0
                    map_needs_redraw = True

            elif event.type == KEYUP:
                if event.key == K_a:
                    camera_left = False
                elif event.key == K_d:
                    camera_right = False
                elif event.key == K_w:
                    camera_up = False
                elif event.key == K_s:
                    camera_down = False

        if player_move_to and not level_is_complete:
            # движение по стрелке
            # перемещение звезд, если возможно
            moved = make_move(map_object, game_object, player_move_to)

            if moved:
                game_object['stepCounter'] += 1
                map_needs_redraw = True

            if is_level_finished(level_object, game_object):
                # если уровень пройден, выводим картинку Solved
                level_is_complete = True
                key_pressed = False

        screen.fill(bg_color)

        if map_needs_redraw:
            map_surf = draw_map(map_object, game_object, level_object['goals'])
            map_needs_redraw = False

        if camera_up and camera_offset_y < max_cam_x_pan:
            camera_offset_y += CAM_MOVE_SPEED
        elif camera_down and camera_offset_y > -max_cam_x_pan:
            camera_offset_y -= CAM_MOVE_SPEED
        if camera_left and camera_offset_x < max_cam_y_pan:
            camera_offset_x += CAM_MOVE_SPEED
        elif camera_right and camera_offset_x > -max_cam_y_pan:
            camera_offset_x -= CAM_MOVE_SPEED

        # меняем map_surf в зависимости от настройки камеры
        map_surf_rect = map_surf.get_rect()
        map_surf_rect.center = (HALF_WIDTH + camera_offset_x, HALF_HEIGHT + camera_offset_y)

        # рисуем map_surf на screen
        screen.blit(map_surf, map_surf_rect)

        screen.blit(level_surf, level_rect)
        step_surf = basic_font.render('Steps: %s' % (game_object['stepCounter']), 1, text_color)
        step_rect = step_surf.get_rect()
        step_rect.bottomleft = (20, HEIGHT - 10)
        screen.blit(step_surf, step_rect)

        if level_is_complete:
            # вывод Solved
            solved_rect = images_dict['solved'].get_rect()
            solved_rect.center = (HALF_WIDTH, HALF_HEIGHT)
            screen.blit(images_dict['solved'], solved_rect)

            if key_pressed:
                return 'solved'

        pygame.display.flip()
        clock.tick()


def is_wall(map_object, x, y):
    # возвращает True если координаты - стена, в других случаях False
    if x < 0 or x >= len(map_object) or y < 0 or y >= len(map_object[x]):
        return False  # вне карты
    elif map_object[x][y] in ('#', 'x'):
        sound_wall.play()
        return True  # стена
    return False


def decorate_map(map_object, startxy):
    # копируем map_object и добавляем декорации

    startx, starty = startxy

    # не меняем оригинал
    map_obj_copy = copy.deepcopy(map_object)

    # удаляем все, кроме стен
    for x in range(len(map_obj_copy)):
        for y in range(len(map_obj_copy[0])):
            if map_obj_copy[x][y] in ('$', '.', '@', '+', '*'):
                map_obj_copy[x][y] = ' '

    flood_fill(map_obj_copy, startx, starty, ' ', 'o')

    for x in range(len(map_obj_copy)):
        for y in range(len(map_obj_copy[0])):

            if map_obj_copy[x][y] == '#':
                if (is_wall(map_obj_copy, x, y - 1) and is_wall(map_obj_copy, x + 1, y)) or \
                        (is_wall(map_obj_copy, x + 1, y) and is_wall(map_obj_copy, x, y + 1)) or \
                        (is_wall(map_obj_copy, x, y + 1) and is_wall(map_obj_copy, x - 1, y)) or \
                        (is_wall(map_obj_copy, x - 1, y) and is_wall(map_obj_copy, x, y - 1)):
                    map_obj_copy[x][y] = 'x'

            elif map_obj_copy[x][y] == ' ' and random.randint(0, 99) < OUTSIDE_DECORATION_PCT:
                map_obj_copy[x][y] = random.choice(list(outside_deco_mapping.keys()))

    return map_obj_copy


def is_blocked(map_object, game_object, x, y):
    # возвращаем True если координаты на карте заблокированы стеной/звездой, иначе False

    if is_wall(map_object, x, y):
        return True

    elif x < 0 or x >= len(map_object) or y < 0 or y >= len(map_object[x]):
        return True  # координат нет на карте

    elif (x, y) in game_object['stars']:
        return True  # звезда блокирует

    return False


def make_move(map_object, game_object, player_move_to):
    # двигаем персонажа, если можно, и возвращаем True, иначе - False

    playerx, playery = game_object['player']
    stars = game_object['stars']

    if player_move_to == UP:
        x_offset = 0
        y_offset = -1
    elif player_move_to == RIGHT:
        x_offset = 1
        y_offset = 0
    elif player_move_to == DOWN:
        x_offset = 0
        y_offset = 1
    elif player_move_to == LEFT:
        x_offset = -1
        y_offset = 0

    if is_wall(map_object, playerx + x_offset, playery + y_offset):
        return False
    else:
        if (playerx + x_offset, playery + y_offset) in stars:
            # если звезда на пути, смотрим, можно ли ее подвинуть
            if not is_blocked(map_object, game_object, playerx + (x_offset * 2), playery + (y_offset * 2)):
                # двигаем
                ind = stars.index((playerx + x_offset, playery + y_offset))
                stars[ind] = (stars[ind][0] + x_offset, stars[ind][1] + y_offset)
                star_sound.play()
            else:
                return False
        game_object['player'] = (playerx + x_offset, playery + y_offset)
        return True


def start_screen():
    # создаем экран перед основной игрой
    title_rect = images_dict['title'].get_rect()
    top_coord = 50
    title_rect.top = top_coord
    title_rect.centerx = HALF_WIDTH
    top_coord += title_rect.height

    intro_text = ['Перемещайте звезды в отведенные места.',
                  'Используйте стрелки, чтобы двигаться, ',
                  'WASD - для смены ракурса, P - для смены персонажа,',
                  'Backspace - для сброса уровня, Esc - для завершения игры.',
                  'N - на уровень вперед, B - на уровень назад.']
    screen.fill(bg_color)
    screen.blit(images_dict['title'], title_rect)

    for i in range(len(intro_text)):
        inst_surf = basic_font.render(intro_text[i], 1, text_color)
        inst_rect = inst_surf.get_rect()
        top_coord += 12
        inst_rect.top = top_coord
        inst_rect.centerx = HALF_WIDTH
        top_coord += inst_rect.height
        screen.blit(inst_surf, inst_rect)

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                terminate()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    terminate()
                return
        pygame.display.flip()
        clock.tick()


def read_levels_file(filename):
    assert os.path.exists(filename), 'Cannot find the level file: %s' % filename
    map_file = open(filename, 'r')
    content = map_file.readlines() + ['\r\n']
    map_file.close()

    levels = []  # список уровней
    level_num = 0
    map_text_lines = []
    map_object = []
    for lineNum in range(len(content)):
        line = content[lineNum].rstrip('\r\n')

        if ';' in line:
            # игнорируем комментарии
            line = line[:line.find(';')]

        if line != '':
            map_text_lines.append(line)
        elif line == '' and len(map_text_lines) > 0:

            # ищем самую длинную строку на карте
            max_width = -1
            for i in range(len(map_text_lines)):
                if len(map_text_lines[i]) > max_width:
                    max_width = len(map_text_lines[i])
            # добавляем пробелы в более короткие строки
            for i in range(len(map_text_lines)):
                map_text_lines[i] += ' ' * (max_width - len(map_text_lines[i]))

            # образуем карту из map_text_lines
            for x in range(len(map_text_lines[0])):
                map_object.append([])
            for y in range(len(map_text_lines)):
                for x in range(max_width):
                    map_object[x].append(map_text_lines[y][x])

            startx = None  # начальная позиция игрока
            starty = None
            goals = []  # списки координат
            stars = []
            for x in range(max_width):
                for y in range(len(map_object[x])):
                    if map_object[x][y] in ('@', '+'):
                        startx = x
                        starty = y
                    if map_object[x][y] in ('.', '+', '*'):
                        goals.append((x, y))
                    if map_object[x][y] in ('$', '*'):
                        stars.append((x, y))

            # проверка уровня
            assert startx and starty, 'Level %s (around line %s) in %s is missing a "@" or "+" to mark the start ' \
                                      'point.' % (
                                          level_num + 1, lineNum, filename)
            assert len(goals) > 0, 'Level %s (around line %s) in %s must have at least one goal.' % (
                level_num + 1, lineNum, filename)
            assert len(stars) >= len(
                goals), 'Level %s (around line %s) in %s is impossible to solve. It has %s goals but only %s stars.' % (
                level_num + 1, lineNum, filename, len(goals), len(stars))

            # создаем level object и начальный game state object.
            game_state_obj = {'player': (startx, starty),
                              'stepCounter': 0,
                              'stars': stars}
            level_obj = {'width': max_width,
                         'height': len(map_object),
                         'map_object': map_object,
                         'goals': goals,
                         'startState': game_state_obj}

            levels.append(level_obj)

            map_text_lines = []
            map_object = []
            game_state_obj = {}
            level_num += 1
    return levels


def flood_fill(map_object, x, y, old_character, new_character):
    # меняем все что относится к oldCharacter на карте на параметры newCharacter

    if map_object[x][y] == old_character:
        map_object[x][y] = new_character

    if x < len(map_object) - 1 and map_object[x + 1][y] == old_character:
        flood_fill(map_object, x + 1, y, old_character, new_character)  # right
    if x > 0 and map_object[x - 1][y] == old_character:
        flood_fill(map_object, x - 1, y, old_character, new_character)  # left
    if y < len(map_object[x]) - 1 and map_object[x][y + 1] == old_character:
        flood_fill(map_object, x, y + 1, old_character, new_character)  # down
    if y > 0 and map_object[x][y - 1] == old_character:
        flood_fill(map_object, x, y - 1, old_character, new_character)  # up
    char_sound.play()


def draw_map(map_object, game_object, goals):
    # рисуем карту
    map_surf_width = len(map_object) * tile_width
    map_surf_height = (len(map_object[0]) - 1) * tile_floor_height + tile_height
    map_surf = pygame.Surface((map_surf_width, map_surf_height))
    map_surf.fill(bg_color)  # start with a blank color on the surface.

    for x in range(len(map_object)):
        for y in range(len(map_object[x])):
            space_rect = pygame.Rect((x * tile_width, y * tile_floor_height, tile_width, tile_height))
            if map_object[x][y] in tile_mapping:
                base_tile = tile_mapping[map_object[x][y]]
            elif map_object[x][y] in outside_deco_mapping:
                base_tile = tile_mapping[' ']

            map_surf.blit(base_tile, space_rect)

            if map_object[x][y] in outside_deco_mapping:
                map_surf.blit(outside_deco_mapping[map_object[x][y]], space_rect)
            elif (x, y) in game_object['stars']:
                if (x, y) in goals:
                    map_surf.blit(images_dict['covered goal'], space_rect)
                map_surf.blit(images_dict['star'], space_rect)
            elif (x, y) in goals:
                map_surf.blit(images_dict['uncovered goal'], space_rect)

            if (x, y) == game_object['player']:
                map_surf.blit(player_images[current_image], space_rect)

    return map_surf


def is_level_finished(level_object, game_object):
    """возвращаем True если все звезды на местах"""
    for goal in level_object['goals']:
        if goal not in game_object['stars']:
            return False
    return True


def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    running = True
    fps = 30
    WIDTH = 800
    HEIGHT = 600
    HALF_WIDTH = int(WIDTH / 2)
    HALF_HEIGHT = int(HEIGHT / 2)

    tile_width = 50
    tile_height = 85
    tile_floor_height = 40

    CAM_MOVE_SPEED = 5

    OUTSIDE_DECORATION_PCT = 20

    bright_blue = (0, 170, 255)
    white = (255, 255, 255)
    bg_color = bright_blue
    text_color = white

    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'

    clock = pygame.time.Clock()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    pygame.display.set_caption('Star Pusher')
    basic_font = pygame.font.Font('freesansbold.ttf', 18)

    images_dict = {'uncovered goal': pygame.image.load('RedSelector.png'),
                   'covered goal': pygame.image.load('Selector.png'),
                   'star': pygame.image.load('Star.png'),
                   'corner': pygame.image.load('Wall_Block_Tall.png'),
                   'wall': pygame.image.load('Wood_Block_Tall.png'),
                   'inside floor': pygame.image.load('Plain_Block.png'),
                   'outside floor': pygame.image.load('Grass_Block.png'),
                   'title': pygame.image.load('star_title.png'),
                   'solved': pygame.image.load('star_solved.png'),
                   'princess': pygame.image.load('princess.png'),
                   'boy': pygame.image.load('boy.png'),
                   'catgirl': pygame.image.load('catgirl.png'),
                   'horngirl': pygame.image.load('horngirl.png'),
                   'pinkgirl': pygame.image.load('pinkgirl.png'),
                   'rock': pygame.image.load('Rock.png'),
                   'short tree': pygame.image.load('Tree_Short.png'),
                   'tall tree': pygame.image.load('Tree_Tall.png'),
                   'ugly tree': pygame.image.load('Tree_Ugly.png')}

    tile_mapping = {'x': images_dict['corner'],
                    '#': images_dict['wall'],
                    'o': images_dict['inside floor'],
                    ' ': images_dict['outside floor']}
    outside_deco_mapping = {'1': images_dict['rock'],
                            '2': images_dict['short tree'],
                            '3': images_dict['tall tree'],
                            '4': images_dict['ugly tree']}
    # current_image = 0
    player_images = [images_dict['princess'],
                     images_dict['boy'],
                     images_dict['catgirl'],
                     images_dict['horngirl'],
                     images_dict['pinkgirl']]
    current_image = 0

    start_screen()

    levels = read_levels_file('starPusherLevels.txt')
    currentLevelIndex = 0

    while running:
        result = run_level(levels, currentLevelIndex)
        if result in ('solved', 'next'):
            currentLevelIndex += 1
            currentLevelIndex += 1
            if currentLevelIndex >= len(levels):
                currentLevelIndex = 0
        elif result == 'back':
            currentLevelIndex -= 1
            if currentLevelIndex < 0:
                currentLevelIndex = len(levels) - 1
        elif result == 'reset':
            pass
