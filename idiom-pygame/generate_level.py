
import json
import os
import random
import sys
import time

# Set recursion limit higher just in case
sys.setrecursionlimit(2000)

class IdiomGenerator:
    def __init__(self, x_block_num=16, y_block_num=16, idiom_count=6):
        self.x_block_num = x_block_num
        self.y_block_num = y_block_num
        self.idiom_count = idiom_count
        self.init_data = [] # The grid
        self.word_dic = {} # Cache for char -> idioms containing char
        self.idiom_dic = {} # Placed idioms info
        self.matrix_record = [] # List of words in the matrix
        self.position_xy = {'x': [], 'y': []} # Occupied starting positions
        
        # Load data
        # Load data
        self.tools_dir = os.path.dirname(os.path.abspath(__file__))
        self.all_idioms = self.load_json('all.json')
        # We also need simple/easy idioms for the starting word, using xdhycycds.json or idiom4.json based on TS usage 
        # In TS game.ts: getRandomWord uses SimpleJson (xdhycycds.json)
        self.simple_idioms = self.load_json('simple.json')

    def load_json(self, filename):
        path = os.path.join(self.tools_dir, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return []

    def get_word_contain_arr(self, char):
        """Finds all idioms containing the character."""
        # This matches game.ts: getWordContainArr
        # In TS: AllJson.filter((i) => i.words.includes(word)).map((j) => j.words)
        return [item['words'] for item in self.all_idioms if char in item['words']]

    def get_random_word(self):
        """Gets a random word from simple idioms."""
        if not self.simple_idioms:
            return "一马当先" # Fallback
        return random.choice(self.simple_idioms)['words']

    def create_data(self):
        """Initializes the empty grid."""
        return [['' for _ in range(self.x_block_num)] for _ in range(self.y_block_num)]

    def get_idiom_begin_position(self, letter, letter_position, idiom, direction):
        """Calculates the starting (x,y) of a new idiom based on an intersection letter."""
        # direction: 0 for horizontal, 1 for vertical
        letter_index = idiom.find(letter)
        x, y = letter_position['x'], letter_position['y']
        
        if direction == 1: # Vertical
            return {'x': x, 'y': y - letter_index}
        else: # Horizontal
            return {'x': x - letter_index, 'y': y}

    def check_words_is_ok(self, word, x, y, direction, ignore_pos):
        """Checks if placing 'word' at (x,y) with 'direction' is valid."""
        
        # 1. Check if word already placed
        if word in self.idiom_dic:
            return False

        # 2. Check overlap with existing start lines (simplified constraint from TS)
        # TS Logic:
        # if direction == 0: if postionXY['y'].includes(y) return false
        # if direction == 1: if postionXY['x'].includes(x) return false
        if direction == 0:
            if y in self.position_xy['y']:
                return False
        if direction == 1:
            if x in self.position_xy['x']:
                return False

        # 3. Check boundaries
        if x < 0 or y < 0:
            return False
            
        # Calculate end position to check boundaries
        if direction == 0:
            if x + len(word) > self.x_block_num:
                return False
        else:
            if y + len(word) > self.y_block_num:
                return False

        # 4. Check collisions and adjacency
        move_arr = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        positions = []
        for index, char in enumerate(word):
            lx = x + index if direction == 0 else x
            ly = y if direction == 0 else y + index
            positions.append({'letter': char, 'x': lx, 'y': ly})

        for pos in positions:
            lx, ly = pos['x'], pos['y']
            
            # Check neighbors
            for dx, dy in move_arr:
                tx, ty = lx + dx, ly + dy
                
                # Check bounds for neighbor check
                if tx < 0 or tx >= self.x_block_num or ty < 0 or ty >= self.y_block_num:
                    continue

                # Ignore the intersection point (where the cross happens)
                if (tx == ignore_pos['x'] and ty == ignore_pos['y']) or \
                   (lx == ignore_pos['x'] and ly == ignore_pos['y']):
                    continue
                
                # If neighbor is occupied, it's a conflict
                if self.init_data[ty][tx]:
                    return False
        
        # 5. Check "later came" intersection
        # Ensure that constructing this word actually connects to the existing grid correctly
        # The simple check `initData[letterY][letterX]` handles if we are overwriting a non-matching char
        exist = False
        for pos in positions:
            lx, ly = pos['x'], pos['y']
            if self.init_data[ly][lx]:
                if self.init_data[ly][lx] != pos['letter']:
                     # Conflict: Grid has char 'A', we want to put 'B'
                    return False
                exist = True # We found the intersection point
        
        if not exist:
             # Should technically not happen if we are extending from existing, 
             # but acts as safety for disjoint placement
             return False

        return True

    def render_data(self, idiom_info, count, direction):
        """Recursive function to place idioms."""
        # idiom_info: {x, y, word}
        word = idiom_info['word']
        x = idiom_info['x']
        y = idiom_info['y']

        # print(f"Rendering: {word} at ({x}, {y}), dir={direction}, remaining={count}")

        if count > 0:
            self.matrix_record.append(word)
        
        self.position_xy['x'].append(x)
        self.position_xy['y'].append(y)

        if count < 1:
            # print("Generation Success!")
            return True

        self.idiom_dic[word] = {
            'word': word,
            'x': x,
            'y': y,
            'direction': direction
        }

        # Place word on grid
        for index, char in enumerate(word):
            # Caching idioms for this char
            if char not in self.word_dic:
                self.word_dic[char] = self.get_word_contain_arr(char)
            
            lx = x + index if direction == 0 else x
            ly = y if direction == 0 else y + index
            
            # In TS logic, randomEmptyIndex adds brackets `[]` for hiding.
            # Here we just place the char for layout generation.
            self.init_data[ly][lx] = char

        # Try to extend from this word
        # In TS, it iterates all placed idioms to find extension points.
        # We will follow a similar breadth/random approach used in the TS code implicitly via recursion on the new state
        
        # NOTE: The TS code iterates `for (const key in idiomDic)` which implies it might branch off ANY already placed word,
        # not just the current one. However, the recursion is `renderData` calls inside the loop.
        # To strictly follow TS logic:
        
        keys = list(self.idiom_dic.keys())
        # Shuffle to randomize expansion
        random.shuffle(keys)

        for key in keys:
            element_word = self.idiom_dic[key]['word']
            element_info = self.idiom_dic[key]
            
            # Iterate characters of the placed idiom
            chars_indices = list(range(len(element_word)))
            random.shuffle(chars_indices) # Randomize which char we extend from

            for index in chars_indices:
                letter = element_word[index]
                letter_arr = self.word_dic.get(letter, [])
                
                # Letter position on grid
                letter_pos = {
                    'x': element_info['x'] + index if element_info['direction'] == 0 else element_info['x'],
                    'y': element_info['y'] if element_info['direction'] == 0 else element_info['y'] + index
                }

                # Try to find a matching idiom
                potential_idioms = letter_arr[:]
                random.shuffle(potential_idioms)

                for next_idiom in potential_idioms:
                    # Calculate new start pos
                    # Next direction is perpendicular (1 - current_dir)
                    next_dir = 1 - element_info['direction']
                    next_start = self.get_idiom_begin_position(letter, letter_pos, next_idiom, next_dir)
                    
                    if self.check_words_is_ok(next_idiom, next_start['x'], next_start['y'], next_dir, {'x': letter_pos['x'], 'y': letter_pos['y']}):
                        # Recurse
                        success = self.render_data({
                            'x': next_start['x'],
                            'y': next_start['y'],
                            'word': next_idiom
                        }, count - 1, next_dir)
                        
                        if success:
                            return True
        
        return False

    def check_around_empty(self, data, letter_x, letter_y):
        """Checks if any surrounding cell is already hidden (has brackets)."""
        move_arr = [[-1, 0], [1, 0], [0, -1], [0, 1]]
        for dx, dy in move_arr:
            tx, ty = letter_x + dx, letter_y + dy
            if 0 <= tx < self.x_block_num and 0 <= ty < self.y_block_num:
                cell = data[ty][tx]
                if cell and cell.startswith('['):
                    return False
        return True

    def hide_words(self, data):
        """Hides characters in the grid."""
        positions = []
        for y in range(self.y_block_num):
            for x in range(self.x_block_num):
                word = data[y][x]
                if word and not word.startswith('['):
                    positions.append({'x': x, 'y': y, 'word': word})
        
        random.shuffle(positions)
        random_empty_count = self.idiom_count + 2
        import copy
        data_copy = copy.deepcopy(data)

        for pos in positions:
            if random_empty_count <= 0:
                break
            x, y, word = pos['x'], pos['y'], pos['word']
            if self.check_around_empty(data_copy, x, y):
                data_copy[y][x] = f"[{word}]"
                random_empty_count -= 1
        
        return data_copy

    def center_content(self):
        """Moves all words to the center of the grid."""
        # Finds bounds
        min_x, max_x = self.x_block_num, -1
        min_y, max_y = self.y_block_num, -1
        
        has_content = False
        for y in range(self.y_block_num):
            for x in range(self.x_block_num):
                if self.init_data[y][x]:
                    if x < min_x: min_x = x
                    if x > max_x: max_x = x
                    if y < min_y: min_y = y
                    if y > max_y: max_y = y
                    has_content = True
        
        if not has_content:
            return

        # Calculate dimensions
        content_width = max_x - min_x + 1
        content_height = max_y - min_y + 1
        
        # Calculate new start positions to center the content
        # Integer division automatically floors, which is fine
        target_min_x = (self.x_block_num - content_width) // 2
        target_min_y = (self.y_block_num - content_height) // 2
        
        offset_x = target_min_x - min_x
        offset_y = target_min_y - min_y
        
        if offset_x == 0 and offset_y == 0:
            return
            
        print(f"Centering: moving by x={offset_x}, y={offset_y}")
            
        new_data = self.create_data()
        
        # Move content
        for y in range(self.y_block_num):
            for x in range(self.x_block_num):
                cell = self.init_data[y][x]
                if cell:
                    new_x = x + offset_x
                    new_y = y + offset_y
                    # Safety check although it should fit if math above is right
                    if 0 <= new_x < self.x_block_num and 0 <= new_y < self.y_block_num:
                        new_data[new_y][new_x] = cell
        
        self.init_data = new_data
        
        # Note: We are not updating self.position_xy or self.idiom_dic logic here 
        # because those are used during generation recursion (renderData).
        # Once generation is done (success=True), we only care about the final grid (`init_data`).
        # If any further logic depended on idiom_dic coordinates, we'd need to update them too,
        # but for the output (grid and word list), this is sufficient.

    def generate(self):
        """Main entry point to generate a level."""
        max_retries = 100
        for i in range(max_retries):
            # print(f"--- Attempt {i+1} ---")
            # Reset
            self.init_data = self.create_data()
            self.word_dic = {}
            self.idiom_dic = {}
            self.matrix_record = []
            self.position_xy = {'x': [], 'y': []}

            # Seed
            first_idiom = self.get_random_word()
            center_x = int(self.x_block_num / 2)
            center_y = int(self.y_block_num / 2)
            rand_x = random.randint(2, 4)
            rand_y = random.randint(-1, 1)
            start_x = center_x - rand_x
            start_y = center_y - rand_y
            
            res = self.render_data({
                'x': start_x,
                'y': start_y,
                'word': first_idiom
            }, self.idiom_count, 0)

            if res:
                self.center_content()
                hidden_grid = self.hide_words(self.init_data)
                return hidden_grid, self.matrix_record
        
        return None, None

    def print_grid(self, data):
        for row in data:
            line = ""
            for cell in row:
                if cell:
                    line += f"[{cell}]"
                else:
                    line += " . "
            print(line)

if __name__ == "__main__":
    generator = IdiomGenerator(x_block_num=10, y_block_num=10, idiom_count=6)
    grid, words = generator.generate()
    
    if grid:
        # User requested JSON array output
        print(json.dumps(grid, ensure_ascii=False))
        # print("Words:", words) # Optional: keep words info in stderr or commented out if strict JSON output is needed for piping
    else:
        print("Failed to generate level after retries.")
