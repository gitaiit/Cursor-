from openpyxl import Workbook
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter
import os

# Create a new workbook with a single sheet
wb = Workbook()
ws = wb.active
ws.title = "Portrait"

# Define colors for the portrait
SKIN_COLOR = "FFE0BD"      # Light skin tone
DRESS_COLOR = "FF69B4"     # Pink for girl's dress
SHIRT_COLOR = "4169E1"     # Blue for boy's shirt
PANTS_COLOR = "000080"     # Navy for pants
HAIR_COLOR = "000000"      # Black for hair
HAND_COLOR = "FFE0BD"      # Skin color for hands

# Create fill objects for each color
skin_fill = PatternFill(start_color=SKIN_COLOR, end_color=SKIN_COLOR, fill_type="solid")
dress_fill = PatternFill(start_color=DRESS_COLOR, end_color=DRESS_COLOR, fill_type="solid")
shirt_fill = PatternFill(start_color=SHIRT_COLOR, end_color=SHIRT_COLOR, fill_type="solid")
pants_fill = PatternFill(start_color=PANTS_COLOR, end_color=PANTS_COLOR, fill_type="solid")
hair_fill = PatternFill(start_color=HAIR_COLOR, end_color=HAIR_COLOR, fill_type="solid")
hand_fill = PatternFill(start_color=HAND_COLOR, end_color=HAND_COLOR, fill_type="solid")

# Set column widths for better visibility (using get_column_letter)
for i in range(1, 15):  # Reduced to 15 columns
    col = get_column_letter(i)
    ws.column_dimensions[col].width = 3

# Set row heights
for i in range(1, 21):
    ws.row_dimensions[i].height = 20

# Girl's head (5x5)
for row in range(2, 7):
    for col in range(2, 7):
        ws.cell(row=row, column=col).fill = skin_fill
        if row == 2 and col in [3, 4, 5]:  # Hair
            ws.cell(row=row, column=col).fill = hair_fill

# Girl's body (5x3)
for row in range(7, 12):
    for col in range(3, 6):
        ws.cell(row=row, column=col).fill = skin_fill

# Girl's dress (5x5)
for row in range(12, 17):
    for col in range(2, 7):
        ws.cell(row=row, column=col).fill = dress_fill

# Girl's legs (3x3)
for row in range(17, 20):
    for col in range(3, 6):
        ws.cell(row=row, column=col).fill = skin_fill

# Boy's head (5x5)
for row in range(2, 7):
    for col in range(8, 13):
        ws.cell(row=row, column=col).fill = skin_fill
        if row == 2 and col in [9, 10, 11]:  # Hair
            ws.cell(row=row, column=col).fill = hair_fill

# Boy's body (5x3)
for row in range(7, 12):
    for col in range(9, 12):
        ws.cell(row=row, column=col).fill = skin_fill

# Boy's shirt (5x5)
for row in range(12, 17):
    for col in range(8, 13):
        ws.cell(row=row, column=col).fill = shirt_fill

# Boy's pants (3x3)
for row in range(17, 20):
    for col in range(9, 12):
        ws.cell(row=row, column=col).fill = pants_fill

# Connected hands (3x3)
for row in range(7, 10):
    for col in range(6, 9):
        ws.cell(row=row, column=col).fill = hand_fill

# Save the workbook
wb.save('portrait.xlsx') 