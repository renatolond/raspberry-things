import badger2040


# Global Constants
WIDTH = badger2040.WIDTH
HEIGHT = badger2040.HEIGHT

COMPANY_HEIGHT = 32 + 16
REST_HEIGHT = HEIGHT - COMPANY_HEIGHT - 2
TEXT_WIDTH = WIDTH - 2

COMPANY_TEXT_SIZE = 3

LEFT_PADDING = 5
NAME_PADDING = 20

BADGE_PATH = "/badges/badge.txt"

DEFAULT_TEXT = """mustelid inc
H. Badger
@hbadger@badger.inc
they/them
"""

# ------------------------------
#      Utility functions
# ------------------------------


# Reduce the size of a string until it fits within a given width
def truncatestring(text, text_size, width):
    while True:
        length = display.measure_text(text, text_size)
        if length > 0 and length > width:
            text = text[:-1]
        else:
            text += ""
            return text


# ------------------------------
#      Drawing functions
# ------------------------------

# Draw the badge, including user text
def draw_badge():
    display.set_pen(0)
    display.clear()

    display.set_pen(0)
    display.set_font("bitmap8")
    handle_size = 4  # A sensible starting scale
    while True:
        handle_length = display.measure_text(handle, handle_size)
        if handle_length >= (TEXT_WIDTH) and handle_size > 1:
            handle_size -= 1
        else:
            break
    handle_height = handle_size*8
    pronouns_size = 3  # A sensible starting scale
    while True:
        pronouns_length = display.measure_text(pronouns, pronouns_size)
        if pronouns_length >= (TEXT_WIDTH) and pronouns_size > 1:
            pronouns_size -= 1
        else:
            break
    pronouns_height = pronouns_size*8

    
    name_height = (REST_HEIGHT - pronouns_height - handle_height)

    # Uncomment this if a white background is wanted behind the company
    # display.set_pen(15)
    # display.rectangle(1, 1, TEXT_WIDTH, COMPANY_HEIGHT - 1)

    # Draw the company
    display.set_pen(15)  # Change this to 0 if a white background is used
    display.set_font("bitmap8")
    company_text_size = display.measure_text("Hello", 3)
    display.text("Hello", (WIDTH // 2) - (company_text_size // 2) , (((COMPANY_TEXT_SIZE - 1) * 8) // 2), WIDTH, COMPANY_TEXT_SIZE)
    company_text_size = display.measure_text("my name is", 2)
    display.text("my name is", (WIDTH // 2) - (company_text_size // 2) , 24 + (16 // 2), WIDTH, 2)

    # Draw a white background behind the name
    display.set_pen(15)
    display.rectangle(1, COMPANY_HEIGHT + 1, TEXT_WIDTH, REST_HEIGHT)

    # Draw the name, scaling it based on the available width
    display.set_pen(0)
    display.set_font("sans")
    name_size = 2.0  # A sensible starting scale
    while True:
        name_length = display.measure_text(name, name_size)
        if name_length >= (TEXT_WIDTH - NAME_PADDING) and name_size >= 0.1:
            name_size -= 0.01
        else:
            display.text(name, (TEXT_WIDTH - name_length) // 2, (name_height // 2) + COMPANY_HEIGHT + 4, WIDTH, name_size)
            break

    display.set_pen(0)
    display.set_font("bitmap8")
    display.text(pronouns, (TEXT_WIDTH - pronouns_length) // 2 + 2, COMPANY_HEIGHT + name_height, WIDTH, pronouns_size)
    display.set_pen(0)
    display.set_font("bitmap8")
    display.text(handle, (TEXT_WIDTH - handle_length) // 2 + 2, COMPANY_HEIGHT + pronouns_height + name_height, WIDTH, handle_size)
    # Draw the first detail's title and text
    #display.set_pen(0)
    #display.set_font("sans")
    #name_length = display.measure_text(detail1_title, DETAILS_TEXT_SIZE)
    #display.text(detail1_title, LEFT_PADDING, HEIGHT - ((DETAILS_HEIGHT * 3) // 2), WIDTH, DETAILS_TEXT_SIZE)
    #display.text(detail1_text, 5 + name_length + DETAIL_SPACING, HEIGHT - ((DETAILS_HEIGHT * 3) // 2), WIDTH, DETAILS_TEXT_SIZE)

    display.update()


# ------------------------------
#        Program setup
# ------------------------------

# Create a new Badger and set it to update NORMAL
display = badger2040.Badger2040()
display.led(128)
display.set_update_speed(badger2040.UPDATE_NORMAL)
display.set_thickness(2)

# Open the badge file
try:
    badge = open(BADGE_PATH, "r")
except OSError:
    with open(BADGE_PATH, "w") as f:
        f.write(DEFAULT_TEXT)
        f.flush()
    badge = open(BADGE_PATH, "r")

# Read in the next 6 lines
_company = badge.readline()        # "mustelid inc"
name = badge.readline()           # "H. Badger"
handle = badge.readline()  # "@hbadger@badger.inc"
pronouns = badge.readline() # "they/them"

# ------------------------------
#       Main program
# ------------------------------

draw_badge()

while True:
    # Sometimes a button press or hold will keep the system
    # powered *through* HALT, so latch the power back on.
    display.keepalive()

    # If on battery, halt the Badger to save power, it will wake up if any of the front buttons are pressed
    display.halt()
