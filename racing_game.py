import pygame
import math
import time

# Инициализация Pygame
pygame.init()

# Константы
WIDTH, HEIGHT = 800, 600
FPS = 60

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (128, 128, 128)

# Параметры овала
OVAL_CENTER_X = WIDTH // 2
OVAL_CENTER_Y = HEIGHT // 2
OVAL_RADIUS_X = 300  # Горизонтальный радиус
OVAL_RADIUS_Y = 150  # Вертикальный радиус
TRACK_WIDTH = 60

# Параметры машины
CAR_WIDTH = 20
CAR_HEIGHT = 10
MAX_SPEED = 300  # Пикселей в секунду
ACCELERATION = 150  # Ускорение пикселей/сек^2
FRICTION = 50  # Трение пикселей/сек^2
TURN_SPEED = 2.5  # Скорость поворота (градусы в секунду)

# Создаем окно
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Racing Game - Oval Track")
clock = pygame.time.Clock()

class Car:
    def __init__(self):
        self.reset()
    
    def reset(self):
        # Начальная позиция (справа на овале)
        self.angle = 0  # Угол на овале (в радианах)
        self.speed = 0  # Текущая скорость
        self.direction = 0  # Направление движения машины (в градусах)
        self.x = OVAL_CENTER_X + OVAL_RADIUS_X
        self.y = OVAL_CENTER_Y
        
        # Для подсчета кругов
        self.start_angle = 0
        self.lap_count = 0
        self.lap_start_time = None
        self.current_lap_time = 0
        self.last_lap_time = None
        self.has_started = False
    
    def update(self, dt, keys):
        # Управление скоростью
        if keys[pygame.K_UP]:
            self.speed += ACCELERATION * dt
        elif keys[pygame.K_DOWN]:
            self.speed -= ACCELERATION * dt
        else:
            # Применение трения
            if self.speed > 0:
                self.speed -= FRICTION * dt
                if self.speed < 0:
                    self.speed = 0
            elif self.speed < 0:
                self.speed += FRICTION * dt
                if self.speed > 0:
                    self.speed = 0
        
        # Ограничение скорости
        self.speed = max(-MAX_SPEED / 2, min(MAX_SPEED, self.speed))
        
        # Поворот машины (только если есть скорость)
        if abs(self.speed) > 10:
            turn_factor = self.speed / MAX_SPEED  # Чем быстрее, тем хуже поворот
            if keys[pygame.K_LEFT]:
                self.direction -= TURN_SPEED * (1 + abs(turn_factor)) * dt * 60
            if keys[pygame.K_RIGHT]:
                self.direction += TURN_SPEED * (1 + abs(turn_factor)) * dt * 60
        
        # Движение машины
        if self.speed != 0:
            rad = math.radians(self.direction)
            self.x += math.cos(rad) * self.speed * dt
            self.y -= math.sin(rad) * self.speed * dt
            
            # Обновляем угол на овале для подсчета кругов
            old_angle = self.angle
            self.angle = math.atan2(self.y - OVAL_CENTER_Y, self.x - OVAL_CENTER_X)
            
            # Проверка на пересечение линии старта/финиша
            if not self.has_started and self.speed > 0:
                self.has_started = True
                self.lap_start_time = time.time()
                self.start_angle = self.angle
            
            if self.has_started and self.lap_start_time is not None:
                # Проверяем пересечение линии старта (угол около 0)
                if old_angle < -math.pi / 2 and self.angle > math.pi / 2:
                    # Завершили круг
                    self.lap_count += 1
                    self.last_lap_time = self.current_lap_time
                    self.lap_start_time = time.time()
                elif old_angle > math.pi / 2 and self.angle < -math.pi / 2 and self.speed < 0:
                    # Завершили круг в обратном направлении
                    self.lap_count += 1
                    self.last_lap_time = self.current_lap_time
                    self.lap_start_time = time.time()
                
                self.current_lap_time = time.time() - self.lap_start_time
    
    def draw(self, surface):
        # Рисуем машину как прямоугольник
        car_surface = pygame.Surface((CAR_WIDTH + 4, CAR_HEIGHT + 4), pygame.SRCALPHA)
        pygame.draw.rect(car_surface, RED, (2, 2, CAR_WIDTH, CAR_HEIGHT))
        
        # Поворачиваем машину
        rotated_car = pygame.transform.rotate(car_surface, self.direction)
        car_rect = rotated_car.get_rect(center=(self.x, self.y))
        surface.blit(rotated_car, car_rect)
    
    def get_state(self):
        """Возвращает текущее состояние для нейросети"""
        return {
            'speed': self.speed,
            'x': self.x,
            'y': self.y,
            'direction': self.direction,
            'angle_on_track': self.angle,
            'current_lap_time': self.current_lap_time,
            'lap_count': self.lap_count
        }


def draw_track(surface):
    """Рисует овальную трассу"""
    # Рисуем асфальт
    pygame.draw.ellipse(surface, GRAY, 
                       (OVAL_CENTER_X - OVAL_RADIUS_X - TRACK_WIDTH // 2,
                        OVAL_CENTER_Y - OVAL_RADIUS_Y - TRACK_WIDTH // 2,
                        OVAL_RADIUS_X * 2 + TRACK_WIDTH,
                        OVAL_RADIUS_Y * 2 + TRACK_WIDTH))
    
    # Рисуем внутреннюю часть (трава)
    pygame.draw.ellipse(surface, GREEN,
                       (OVAL_CENTER_X - OVAL_RADIUS_X + TRACK_WIDTH // 2,
                        OVAL_CENTER_Y - OVAL_RADIUS_Y + TRACK_WIDTH // 2,
                        OVAL_RADIUS_X * 2 - TRACK_WIDTH,
                        OVAL_RADIUS_Y * 2 - TRACK_WIDTH))
    
    # Рисуем линию старта/финиша
    start_x = OVAL_CENTER_X + OVAL_RADIUS_X
    pygame.draw.line(surface, WHITE,
                    (start_x, OVAL_CENTER_Y - TRACK_WIDTH // 2),
                    (start_x, OVAL_CENTER_Y + TRACK_WIDTH // 2), 3)
    
    # Чередующиеся клетки на линии финиша
    checkered_size = 5
    for i in range(-TRACK_WIDTH // 2, TRACK_WIDTH // 2, checkered_size * 2):
        pygame.draw.rect(surface, WHITE,
                        (start_x - 2, OVAL_CENTER_Y + i, 4, checkered_size))


def draw_ui(surface, car):
    """Рисует пользовательский интерфейс"""
    font = pygame.font.Font(None, 36)
    
    # Текущая скорость
    speed_text = font.render(f"Speed: {abs(car.speed):.1f}", True, BLACK)
    surface.blit(speed_text, (10, 10))
    
    # Время текущего круга
    if car.has_started:
        lap_text = font.render(f"Lap Time: {car.current_lap_time:.2f}s", True, BLACK)
        surface.blit(lap_text, (10, 50))
    else:
        lap_text = font.render("Lap Time: --.--s", True, BLACK)
        surface.blit(lap_text, (10, 50))
    
    # Количество кругов
    laps_text = font.render(f"Laps: {car.lap_count}", True, BLACK)
    surface.blit(laps_text, (10, 90))
    
    # Последнее время круга
    if car.last_lap_time is not None:
        last_lap_text = font.render(f"Last Lap: {car.last_lap_time:.2f}s", True, BLUE)
        surface.blit(last_lap_text, (10, 130))
    
    # Инструкция
    instr_font = pygame.font.Font(None, 24)
    instr_text = instr_font.render("UP/DOWN: Accelerate/Brake  LEFT/RIGHT: Steer  R: Reset", True, BLACK)
    surface.blit(instr_text, (10, HEIGHT - 30))


def main():
    car = Car()
    running = True
    
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time в секундах
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    car.reset()
        
        # Получаем состояние клавиш
        keys = pygame.key.get_pressed()
        
        # Обновляем машину
        car.update(dt, keys)
        
        # Отрисовка
        screen.fill(WHITE)
        draw_track(screen)
        car.draw(screen)
        draw_ui(screen, car)
        
        pygame.display.flip()
    
    pygame.quit()


if __name__ == "__main__":
    main()
