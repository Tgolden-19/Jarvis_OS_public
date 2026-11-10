import pygame

class Button:
    def __init__(
        self,
        text,
        font,
        center_pos,
        text_color=(0, 0, 0),
        button_color=(206, 255, 218),
        hover_color=(100, 160, 210),
        border_color=(0, 0, 0),
        border_width=4,
        padding=10
    ):
        self.text = text
        self.font = font
        self.center_pos = center_pos

        self.text_color = text_color
        self.button_color = button_color
        self.hover_color = hover_color
        self.border_color = border_color
        self.border_width = border_width
        self.padding = padding

        self._create_surfaces()

    def _create_surfaces(self):
        # Render text
        self.text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = self.text_surface.get_rect()

        # Button size = text size + padding
        width = text_rect.width + self.padding * 2
        height = text_rect.height + self.padding * 2

        # Create button rect
        self.rect = pygame.FRect(0, 0, width, height)
        self.rect.center = self.center_pos

        # Store inner rect (area inside border)
        self.inner_rect = pygame.FRect(
            self.rect.left + self.border_width,
            self.rect.top + self.border_width,
            self.rect.width - self.border_width * 2,
            self.rect.height - self.border_width * 2
        )

    def update_text(self, text):
        self.text = text
        self._create_surfaces()

    def draw(self, surface, highlighted:bool, x=-1, y=-1):
        if x != -1 and y != -1:
            self.center_pos = (x, y)
            self._create_surfaces()
        mouse_pos = pygame.mouse.get_pos()


        # Change color on hover
        if self.rect.collidepoint(mouse_pos) or highlighted:
            color = self.border_color
        else:
            color = self.button_color

        # Draw border (black box)
        pygame.draw.rect(surface, color, self.rect)

        # Draw inner button
        pygame.draw.rect(surface, self.button_color, self.inner_rect)

        # Draw text centered
        text_rect = self.text_surface.get_rect(center=self.rect.center)
        surface.blit(self.text_surface, text_rect)

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False
    