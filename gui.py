
# Requirements:
#   pip install pygame python-chess

import os
import sys
import time
import threading
from enum import Enum

import pygame
import chess
import chess.engine

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SQUARE_SIZE = 80
BOARD_SIZE = 8 * SQUARE_SIZE
SIDE_PANEL_W = 300
WIN_SIZE = (BOARD_SIZE + SIDE_PANEL_W, BOARD_SIZE)
FPS = 60

START_TIME = 300
ENGINE_PATH = os.path.join(os.path.dirname(__file__), "./engine")

LIGHT = (240, 217, 181)
DARK = (181, 136,  99)
BLUE = ( 66, 135, 245)

# ---------------------------------------------------------------------------
# Audio System
# ---------------------------------------------------------------------------

class ChessAudio:
    def __init__(self):
        """Initialize pygame mixer and load sound effects"""
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.sounds = {}
        self.audio_enabled = True
        self.load_sounds()
    
    def load_sounds(self):
        """Load all chess sound effects"""
        sound_dir = os.path.join(os.path.dirname(__file__), "assets", "sounds")
        
        # Create default sounds directory if it doesn't exist
        if not os.path.exists(sound_dir):
            os.makedirs(sound_dir, exist_ok=True)
            print(f"Created sound directory: {sound_dir}")
            print("Please add the following sound files:")
            for sound_name in ["move", "capture", "check", "castle", "game_start", "game_end"]:
                print(f"  - {sound_name}.wav or {sound_name}.ogg")
        
        # Sound file mappings
        sound_files = {
            'move': ['move.wav', 'move.ogg'],
            'capture': ['capture.wav', 'capture.ogg'],
            'check': ['check.wav', 'check.ogg'],
            'castle': ['castle.wav', 'castle.ogg'],
            'game_start': ['game_start.wav', 'game_start.ogg'],
            'game_end': ['game_end.wav', 'game_end.ogg'],
        }
        
        # Try to load each sound file
        for sound_name, filenames in sound_files.items():
            sound_loaded = False
            for filename in filenames:
                filepath = os.path.join(sound_dir, filename)
                if os.path.exists(filepath):
                    try:
                        self.sounds[sound_name] = pygame.mixer.Sound(filepath)
                        sound_loaded = True
                        print(f"Loaded sound: {filename}")
                        break
                    except pygame.error as e:
                        print(f"Failed to load {filename}: {e}")
            
            if not sound_loaded:
                # Create a simple beep as fallback
                self.sounds[sound_name] = self.create_beep(sound_name)
                print(f"Using fallback beep for: {sound_name}")
    
    def create_beep(self, sound_type):
        """Create a simple beep sound as fallback"""
        duration = 0.1
        sample_rate = 22050
        frames = int(duration * sample_rate)
        
        # Different frequencies for different sounds
        frequencies = {
            'move': 440,      # A4
            'capture': 523,   # C5
            'check': 659,     # E5
            'castle': 349,    # F4
            'game_start': 523, # C5
            'game_end': 261    # C4
        }
        
        freq = frequencies.get(sound_type, 440)
        
        # Generate sine wave
        arr = []
        for i in range(frames):
            wave = 4096 * pygame.math.sin(2 * pygame.math.pi * freq * i / sample_rate)
            arr.append([int(wave), int(wave)])
        
        sound = pygame.sndarray.make_sound(pygame.array.array('i', arr))
        sound.set_volume(0.3)  # Make it quieter
        return sound
    
    def play_sound(self, sound_name):
        """Play a sound effect"""
        if self.audio_enabled and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except pygame.error as e:
                print(f"Failed to play sound {sound_name}: {e}")
    
    def toggle_audio(self):
        """Toggle audio on/off"""
        self.audio_enabled = not self.audio_enabled
        return self.audio_enabled
    
    def play_move_sound(self, board, move):
        """Play appropriate sound based on move type"""
        if not self.audio_enabled:
            return
        
        # Determine sound based on move characteristics
        if board.is_castling(move):
            self.play_sound('castle')
        elif board.is_capture(move):
            self.play_sound('capture')
        else:
            self.play_sound('move')
        
        # Check for check after the move is made
        # Note: This should be called after the move is pushed to the board
    
    def play_check_sound(self):
        """Play check sound"""
        self.play_sound('check')
    
    def play_game_start_sound(self):
        """Play game start sound"""
        self.play_sound('game_start')
    
    def play_game_end_sound(self):
        """Play game end sound"""
        self.play_sound('game_end')

# ---------------------------------------------------------------------------
# Helper: load piece images
# ---------------------------------------------------------------------------

def load_piece_images(square_px=SQUARE_SIZE):
    piece_dir = os.path.join(os.path.dirname(__file__), "assets/pieces")
    images = {}
    for color in ('w', 'b'):
        for letter in ('K','Q','R','B','N','P'):
            key = color + letter
            path = os.path.join(piece_dir, f"{key}.png")
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                images[key] = pygame.transform.smoothscale(img, (square_px, square_px))
            else:
                # Create a simple colored rectangle as fallback
                img = pygame.Surface((square_px, square_px), pygame.SRCALPHA)
                color_val = (255, 255, 255) if color == 'w' else (0, 0, 0)
                pygame.draw.rect(img, color_val, (0, 0, square_px, square_px))
                font = pygame.font.Font(None, 36)
                text = font.render(letter, True, (255, 0, 0) if color == 'w' else (255, 255, 0))
                text_rect = text.get_rect(center=(square_px//2, square_px//2))
                img.blit(text, text_rect)
                images[key] = img
    return images

PIECE_IMAGES = {}  # filled after pygame.init()

# ---------------------------------------------------------------------------
# Simple chess clock
# ---------------------------------------------------------------------------

class Clock:
    def __init__(self, start_sec=START_TIME):
        self.remaining = {
            chess.WHITE: float(start_sec),
            chess.BLACK: float(start_sec)
        }
        self.last_tick = time.time()

    def start_turn(self):
        self.last_tick = time.time()

    def stop_turn(self, side_to_move):
        now = time.time()
        self.remaining[side_to_move] -= now - self.last_tick

    def flag(self):
        return any(t <= 0 for t in self.remaining.values())

    def draw(self, screen, turn_color):
        font = pygame.font.SysFont("Consolas", 28)
        for side, y in ((chess.WHITE,20),(chess.BLACK,55)):
            secs = max(0,int(self.remaining[side]))
            txt = time.strftime("%M:%S", time.gmtime(secs))
            col = BLUE if side == turn_color else (0,0,0)
            label = font.render(f"{'White' if side==chess.WHITE else 'Black'}: {txt}", True, col)
            screen.blit(label, (BOARD_SIZE+20, y))

# ---------------------------------------------------------------------------
# Scrollable Move Log (abbreviated for space)
# ---------------------------------------------------------------------------

class ScrollableMoveLog:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.moves = []
        self.current_move_number = 1
        self.waiting_for_black = False
        self.line_height = 18
        self.visible_lines = (height - 60)//self.line_height
        self.scroll_y = 0
        self.max_scroll = 0

    def add_move(self, san, is_white):
        if is_white:
            self.moves.append([self.current_move_number, san, ""])
            self.waiting_for_black = True
        else:
            if self.waiting_for_black and self.moves:
                self.moves[-1][2] = san
                self.current_move_number += 1
                self.waiting_for_black = False
            else:
                self.moves.append([self.current_move_number, "", san])
                self.current_move_number += 1
        self._update_scroll_limits()
        self._auto_scroll_to_bottom()

    def clear(self):
        self.moves = []
        self.current_move_number = 1
        self.waiting_for_black = False
        self.scroll_y = 0
        self.max_scroll = 0

    def _update_scroll_limits(self):
        total = len(self.moves)
        if total > self.visible_lines:
            self.max_scroll = (total-self.visible_lines)*self.line_height
        else:
            self.max_scroll = 0
        self.scroll_y = max(0, min(self.scroll_y, self.max_scroll))

    def _auto_scroll_to_bottom(self):
        self.scroll_y = self.max_scroll

    def handle_mouse_wheel(self, e):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            amt = e.y*self.line_height*3
            self.scroll_y = max(0, min(self.scroll_y-amt, self.max_scroll))
            return True
        return False

    def draw(self, screen):
        content = pygame.Rect(self.rect.x, self.rect.y, self.rect.width-5, self.rect.height)
        pygame.draw.rect(screen, (240,240,240), content)
        pygame.draw.rect(screen, (0,0,0), content, 1)

        title = pygame.font.SysFont("Verdana",18,True).render("Move Log",True,(0,0,0))
        screen.blit(title, (self.rect.x+10, self.rect.y+5))
        
        mv_area = pygame.Rect(self.rect.x, self.rect.y+50, content.width, self.rect.height-50)
        oc = screen.get_clip()
        screen.set_clip(mv_area)

        start = int(self.scroll_y//self.line_height)
        end = min(len(self.moves), start+self.visible_lines+2)
        y0 = mv_area.y - (self.scroll_y%self.line_height)
        font = pygame.font.SysFont("Consolas",16)
        for i in range(start, end):
            mn,ws,bs = self.moves[i]
            txt = f"{mn:2d} {ws:8s} {bs:8s}"
            y = y0 + (i-start)*self.line_height
            if mv_area.y <= y < mv_area.bottom:
                screen.blit(font.render(txt,True,(0,0,0)), (self.rect.x+10, y))

        screen.set_clip(oc)

# ---------------------------------------------------------------------------
# UCI Engine wrapper
# ---------------------------------------------------------------------------

class UCIEngine:
    def __init__(self, path=ENGINE_PATH):
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(path)
        except Exception as e:
            print("Engine start failed:", e)
            self.engine = None
        self.lock = threading.Lock()

    def best_move(self, board, thinking_time=1.5):
        if not self.engine:
            return None
        with self.lock:
            try:
                return self.engine.play(board, chess.engine.Limit(time=thinking_time)).move
            except:
                return None

    def quit(self):
        if self.engine:
            with self.lock:
                try:
                    self.engine.quit()
                except:
                    pass

# ---------------------------------------------------------------------------
# GUI modes
# ---------------------------------------------------------------------------

class Mode(Enum):
    HUMAN_VS_HUMAN   = 0
    HUMAN_VS_ENGINE = 1
    ENGINE_VS_HUMAN = 2
    ENGINE_VS_ENGINE= 3
    ANALYSIS        = 4

MODE_NAMES = {
    Mode.HUMAN_VS_HUMAN:   "H-H",
    Mode.HUMAN_VS_ENGINE:  "H-E",
    Mode.ENGINE_VS_HUMAN:  "E-H",
    Mode.ENGINE_VS_ENGINE: "E-E",
    Mode.ANALYSIS:         "ANA"
}

# ---------------------------------------------------------------------------
# Main GUI with Audio
# ---------------------------------------------------------------------------

class ChessGUI:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("SynapseChess")
        self.screen = pygame.display.set_mode(WIN_SIZE)
        self.clock  = pygame.time.Clock()

        global PIECE_IMAGES
        PIECE_IMAGES = load_piece_images()

        # Initialize audio system
        self.audio = ChessAudio()

        self.board = chess.Board()
        self.engine = UCIEngine()
        self.game_clock = Clock()
        self.move_log = ScrollableMoveLog(BOARD_SIZE+20, 180, 180, 280)
        self.mode = Mode.HUMAN_VS_ENGINE

        self.selected_sq = None
        self.valid_dest_sqs = []
        self.last_move = None
        self.running = True

        self.engine_thread = None
        self.pending_engine_move = None

        # Audio toggle button
        self.audio_btn_rect = pygame.Rect(BOARD_SIZE+20, 130, 160, 28)

        self.game_clock.start_turn()
        self.maybe_start_engine_think()
        
        # Play game start sound
        self.audio.play_game_start_sound()

    def launch(self):
        while self.running:
            self.handle_events()
            self.handle_engine()
            self.draw()
            self.clock.tick(FPS)
        self.engine.quit()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        keys = pygame.key.get_pressed()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                self.running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_n:
                    self.new_game()
                elif e.key == pygame.K_SPACE:
                    self.change_mode()
                elif e.key == pygame.K_m:  # Toggle audio with 'M' key
                    enabled = self.audio.toggle_audio()
                    print(f"Audio {'enabled' if enabled else 'disabled'}")
                elif e.key == pygame.K_ESCAPE:
                    self.selected_sq = None
                    self.valid_dest_sqs = []
            elif e.type == pygame.MOUSEWHEEL:
                self.move_log.handle_mouse_wheel(e)
            elif e.type == pygame.MOUSEBUTTONDOWN:
                if e.button == 1:
                    if self.audio_btn_rect.collidepoint(e.pos):
                        enabled = self.audio.toggle_audio()
                        print(f"Audio {'enabled' if enabled else 'disabled'}")
                    else:
                        self.on_click(e.pos)

    def change_mode(self):
        """Change mode with audio feedback and board reset"""
        self.stop_engine()
        
        modes = list(Mode)
        idx = (modes.index(self.mode) + 1) % len(modes)
        self.mode = modes[idx]
        
        # Reset board and game state
        self.board.reset()
        self.selected_sq = None
        self.valid_dest_sqs = []
        self.last_move = None
        self.pending_engine_move = None
        
        self.game_clock = Clock()
        self.game_clock.start_turn()
        self.move_log.clear()
        
        print(f"Mode changed to: {MODE_NAMES[self.mode]}")
        
        # Play game start sound for new mode
        self.audio.play_game_start_sound()
        self.maybe_start_engine_think()

    def stop_engine(self):
        """Stop any ongoing engine calculations"""
        self.pending_engine_move = None

    def new_game(self):
        """Start a new game in current mode"""
        self.stop_engine()
        
        self.board.reset()
        self.selected_sq = None
        self.valid_dest_sqs = []
        self.pending_engine_move = None
        self.game_clock = Clock()
        self.move_log.clear()
        self.last_move = None
        
        self.game_clock.start_turn()
        self.audio.play_game_start_sound()
        self.maybe_start_engine_think()

    def on_click(self, pos):
        if self.mode == Mode.ENGINE_VS_ENGINE:
            return
        x,y = pos
        if x>=BOARD_SIZE or y>=BOARD_SIZE:
            return
        f = x//SQUARE_SIZE
        r = 7 - y//SQUARE_SIZE
        sq = chess.square(f,r)
        piece = self.board.piece_at(sq)

        if self.selected_sq is None:
            if piece and (
               (self.board.turn==chess.WHITE and piece.color==chess.WHITE and
                self.mode in (Mode.HUMAN_VS_HUMAN,Mode.HUMAN_VS_ENGINE)) or
               (self.board.turn==chess.BLACK and piece.color==chess.BLACK and
                self.mode in (Mode.HUMAN_VS_HUMAN,Mode.ENGINE_VS_HUMAN)) or
               self.mode==Mode.ANALYSIS):
                self.selected_sq = sq
                self.valid_dest_sqs = [
                    m.to_square for m in self.board.legal_moves
                    if m.from_square==sq
                ]
        else:
            mv = chess.Move(self.selected_sq, sq)
            if mv in self.board.legal_moves:
                self.make_move(mv)
            else:
                self.selected_sq=None
                self.valid_dest_sqs=[]

    def make_move(self, move):
        """Make a move with audio feedback"""
        self.game_clock.stop_turn(self.board.turn)
        san = self.board.san(move)
        is_white = (self.board.turn==chess.WHITE)
        
        # Handle pawn promotion
        if (self.board.piece_at(move.from_square).piece_type==chess.PAWN and
            chess.square_rank(move.to_square) in (0,7) and move.promotion is None):
            move.promotion = chess.QUEEN
            san = self.board.san(move)

        # Play appropriate sound before making the move
        self.audio.play_move_sound(self.board, move)

        # Make the move
        self.board.push(move)
        self.last_move = move
        self.move_log.add_move(san, is_white)
        
        # Check for check after the move
        if self.board.is_check():
            # Small delay to let move sound play first
            pygame.time.wait(200)
            self.audio.play_check_sound()
        
        # Check for game end
        if self.board.is_game_over():
            pygame.time.wait(400)
            self.audio.play_game_end_sound()

        if self.mode!=Mode.ANALYSIS:
            self.game_clock.start_turn()
        self.selected_sq=None
        self.valid_dest_sqs=[]
        self.maybe_start_engine_think()

    def maybe_start_engine_think(self):
        if not self.engine.engine:
            return
        if self.engine_thread and self.engine_thread.is_alive():
            return
        if self.board.is_game_over():
            return
        side = self.board.turn
        if ((side==chess.WHITE and self.mode in (Mode.ENGINE_VS_HUMAN,Mode.ENGINE_VS_ENGINE))
            or (side==chess.BLACK and self.mode in (Mode.HUMAN_VS_ENGINE,Mode.ENGINE_VS_ENGINE))):
            self.engine_thread = threading.Thread(target=self.engine_calculate, daemon=True)
            self.engine_thread.start()

    def engine_calculate(self):
        self.pending_engine_move = self.engine.best_move(self.board)

    def handle_engine(self):
        if self.pending_engine_move:
            self.make_move(self.pending_engine_move)
            self.pending_engine_move = None

    def draw(self):
        self.screen.fill((0,0,0))
        self.draw_board()
        self.draw_side_panel()
        pygame.display.flip()

    def draw_board(self):
        # Base squares
        for rank in range(8):
            for file in range(8):
                sq = chess.square(file,7-rank)
                rect = pygame.Rect(file*SQUARE_SIZE, rank*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                color = LIGHT if (file+rank)%2==0 else DARK
                pygame.draw.rect(self.screen, color, rect)

        # Highlight last move
        if self.last_move:
            surf = pygame.Surface((SQUARE_SIZE,SQUARE_SIZE), pygame.SRCALPHA)
            surf.fill((255,255,0,90))
            for sq in (self.last_move.from_square, self.last_move.to_square):
                f = chess.square_file(sq)
                r = chess.square_rank(sq)
                self.screen.blit(surf, (f*SQUARE_SIZE, (7-r)*SQUARE_SIZE))

        # Highlight check
        if self.board.is_check():
            ksq = self.board.king(self.board.turn)
            if ksq is not None:
                surf = pygame.Surface((SQUARE_SIZE,SQUARE_SIZE), pygame.SRCALPHA)
                surf.fill((255,0,0,100))
                f = chess.square_file(ksq)
                r = chess.square_rank(ksq)
                self.screen.blit(surf, (f*SQUARE_SIZE, (7-r)*SQUARE_SIZE))

        # Highlight selection and legal destinations
        for rank in range(8):
            for file in range(8):
                sq = chess.square(file,7-rank)
                rect = pygame.Rect(file*SQUARE_SIZE, rank*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                if sq == self.selected_sq or sq in self.valid_dest_sqs:
                    pygame.draw.rect(self.screen, BLUE, rect, 3)

        # Draw pieces
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece:
                f = chess.square_file(sq)
                r = 7 - chess.square_rank(sq)
                key = ('w' if piece.color==chess.WHITE else 'b') + piece.symbol().upper()
                self.screen.blit(PIECE_IMAGES[key], (f*SQUARE_SIZE, r*SQUARE_SIZE))

    def draw_side_panel(self):
        pygame.draw.rect(self.screen, (225,225,225), pygame.Rect(BOARD_SIZE,0,SIDE_PANEL_W,BOARD_SIZE))
        
        font = pygame.font.SysFont("Verdana",22,True)
        self.screen.blit(font.render(f"Mode: {MODE_NAMES[self.mode]}",True,(0,0,0)), (BOARD_SIZE+20,100))

        # Audio toggle button
        btn_color = (100, 255, 100) if self.audio.audio_enabled else (255, 100, 100)
        pygame.draw.rect(self.screen, btn_color, self.audio_btn_rect, border_radius=4)
        btn_text = "Audio: ON" if self.audio.audio_enabled else "Audio: OFF"
        btn_font = pygame.font.SysFont("Verdana", 16)
        text_surf = btn_font.render(btn_text, True, (0,0,0))
        text_rect = text_surf.get_rect(center=self.audio_btn_rect.center)
        self.screen.blit(text_surf, text_rect)

        if self.mode!=Mode.ANALYSIS:
            self.game_clock.draw(self.screen, self.board.turn)

        self.move_log.draw(self.screen)

        # Game outcome
        outcome = None
        if self.game_clock.flag() and self.mode!=Mode.ANALYSIS:
            outcome = "Time forfeit"
        elif self.board.is_checkmate():
            winner = "White" if self.board.turn==chess.BLACK else "Black"
            outcome = f"{winner} wins"
        elif self.board.is_stalemate():
            outcome = "Stalemate"
        elif self.board.is_insufficient_material():
            outcome = "Draw"
        elif self.board.is_repetition(3) or self.board.is_fivefold_repetition():
            outcome = "Repetition"
        elif self.board.is_fifty_moves():
            outcome = "50-move rule"
        
        if outcome:
            of = pygame.font.SysFont("Verdana",18,True)
            lbl = of.render(outcome,True,BLUE)
            tr = lbl.get_rect(centerx=BOARD_SIZE+SIDE_PANEL_W//2, y=480)
            self.screen.blit(lbl, tr)

        # Instructions
        font2 = pygame.font.SysFont("Consolas",14)
        lines = [
            "N  : new game",
            "SPACE: change mode + reset", 
            "M  : toggle audio",
            "ESC  : cancel select",
            "",
            "Click piece then target",
            "Mouse wheel: scroll moves",
            "",
            "Audio Effects:",
            "♪ Move sounds",
            "♪ Capture sounds", 
            "♪ Check alerts",
            "♪ Castling sounds"
        ]
        y=500
        for txt in lines:
            if y>BOARD_SIZE-20: break
            self.screen.blit(font2.render(txt,True,(0,0,0)), (BOARD_SIZE+10,y))
            y+=16

if __name__ == "__main__":
    ChessGUI().launch()
