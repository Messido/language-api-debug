import pandas as pd
import os

# Unified Schema for Match Pairs (A1 & B1)
# Removed 'Level' column.
# Added 'Unique ID' column.

data = [
    # Description Row
    {
        "Unique ID": "Unique Identifier (e.g. MP001)",
        "Type": "Card Type (Text-Text or Audio-Text)",
        "Prompt": "Question/Audio Text (French)",
        "Target": "Answer/Translation (English)",
        "Instruction_FR": "Instruction (French)",
        "Instruction_EN": "Instruction (English)"
    },
    # A1 Data (Text-Text)
    {
        "Unique ID": "MP001",
        "Type": "Text-Text",
        "Prompt": "Chien",       # French Word
        "Target": "Dog",         # English Word
        "Instruction_FR": "Associez les paires",
        "Instruction_EN": "Match the pairs"
    },
    {
        "Unique ID": "MP002",
        "Type": "Text-Text",
        "Prompt": "Chat",
        "Target": "Cat",
        "Instruction_FR": "Associez les paires",
        "Instruction_EN": "Match the pairs"
    },
    # B1 Data (Audio-Text)
    {
        "Unique ID": "MP003",
        "Type": "Audio-Text",
        "Prompt": "Chien",       # Audio Text
        "Target": "Dog",         # Match
        "Instruction_FR": "Associez les paires",
        "Instruction_EN": "Match the pairs"
    },
    {
        "Unique ID": "MP004",
        "Type": "Audio-Text",
        "Prompt": "Chat",
        "Target": "Cat",
        "Instruction_FR": "Associez les paires",
        "Instruction_EN": "Match the pairs"
    }
]

df_unified = pd.DataFrame(data)

# Output Path
output_file = "MatchPairsSchema.xlsx"

# Write to Excel
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df_unified.to_excel(writer, sheet_name='MatchPairs_Unified', index=False)

print(f"Created {output_file} with sheet 'MatchPairs_Unified'")
